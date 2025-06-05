# main_scheduler.py

import os
import time
import argparse
import traceback
from datetime import datetime

from utils import termination_handler
from utils.logger import logger
from utils.json_manager import load_json, save_json
from app_core.analytics.strategy_profit_calculator import calculate_strategy_profits
from interface.reports.performance_report import generate_performance_report
from utils.notifier import send_alert
from app_core.controller.entry_trigger import EntrySignalChecker
from app_core.controller.exit_trader import ExitTrader
from app_core.infra_control.capital_allocator import allocate_capital_weights  # ✅ 자본 배분 로직 연동

# 설정 파일 로드
CONFIG = load_json("config/config.json")

LOCK_FILE = CONFIG.get("lock_file", "runtime/scheduler.lock")
HEALTH_FILE = CONFIG.get("health_file", "runtime/healthcheck.json")
TERMINATE_FILE = CONFIG.get("terminate_file", "runtime/terminate.flag")
STRATEGY_LOG_DIR = CONFIG.get("strategy_log_dir", "data_io/json_store/trade_log")
SCORE_FILE_PATH = CONFIG.get("score_file_path", "data_io/json_store/strategy_scores.json")
REPORT_HTML_PATH = CONFIG.get("report_html_path", "interface/reports/strategy_report.html")
REPORT_PDF_PATH = CONFIG.get("report_pdf_path", "interface/reports/strategy_report.pdf")
STOP_ON_ERROR = CONFIG.get("stop_on_error", False)
ALERT_ENABLED = CONFIG.get("alert_enabled", True)
ROI_FILTER = CONFIG.get("roi_filter", 0.5)
INCLUDE_STRATEGIES = CONFIG.get("include_strategies", [])  # 비워두면 전체


def main_loop(interval_sec):
    if termination_handler.is_running():
        logger.error("❗ 이미 실행 중입니다. 중복 실행 방지를 위해 종료합니다.")
        return

    termination_handler.create_lock()
    logger.info("✅ 메인 스케줄러 시작됨.")
    termination_handler.write_health("started")

    entry_checker = EntrySignalChecker()
    exit_checker = ExitTrader()

    try:
        while True:
            if termination_handler.check_termination():
                logger.warning("🛑 종료 플래그 발견. 루프를 종료합니다.")
                break

            try:
                logger.info("🔍 진입 시그널 체크 중...")
                entry_checker.check()

                logger.info("📤 청산 시그널 체크 중...")
                exit_checker.check()

                logger.info("📈 전략별 수익률 계산 중...")
                strategy_scores = calculate_strategy_profits(log_dir=STRATEGY_LOG_DIR)

                if INCLUDE_STRATEGIES:
                    strategy_scores = [s for s in strategy_scores if s['strategy_name'] in INCLUDE_STRATEGIES]

                strategy_scores = [s for s in strategy_scores if s.get('roi', 0) >= ROI_FILTER]
                save_json(SCORE_FILE_PATH, strategy_scores)

                logger.info("📊 상위 전략 요약:")
                top_strategies = sorted(strategy_scores, key=lambda x: x.get("roi", 0), reverse=True)[:3]
                for s in top_strategies:
                    logger.info(f" - {s['strategy_name']} | ROI: {s.get('roi', 0):.2f}%")

                logger.info("📄 리포트 생성 중...")
                try:
                    generate_performance_report(
                        metrics=strategy_scores,
                        output_path=REPORT_HTML_PATH,
                        pdf_output_path=REPORT_PDF_PATH
                    )
                except Exception as report_err:
                    logger.warning(f"⚠️ 리포트 생성 실패: {report_err}")
                    if ALERT_ENABLED:
                        send_alert("📄 리포트 생성 실패!", level="warning")

                # ✅ 전략 자본 비중 자동 계산 추가
                allocate_capital_weights()

                termination_handler.write_health("running")
                logger.success(f"✅ 루프 완료. {interval_sec}초 후 재시작.")
                time.sleep(interval_sec)

            except Exception as e:
                logger.error(f"🚨 루프 예외 발생: {e}")
                logger.exception("🔍 상세 에러:")
                if ALERT_ENABLED:
                    send_alert(f"❗ 루프 예외 발생: {e}", level="critical")
                if STOP_ON_ERROR:
                    break
                time.sleep(30)

    except KeyboardInterrupt:
        logger.warning("🛑 사용자 중단 요청 감지됨. 루프 종료 중...")

    finally:
        termination_handler.write_health("stopped")
        termination_handler.remove_lock()
        logger.info("🧹 종료 정리 완료. 시스템 종료됨.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=CONFIG.get("loop_interval_sec", 180), help="루프 실행 간격 (초)")
    args = parser.parse_args()
    main_loop(args.interval)
