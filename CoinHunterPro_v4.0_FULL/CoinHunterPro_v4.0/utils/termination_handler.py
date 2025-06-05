# utils/termination_handler.py

import os
import psutil
from datetime import datetime
from utils.json_manager import save_json
from utils.logger import logger
from dotenv import load_dotenv

load_dotenv()

# 기본 경로 (config.json에서 읽지 않고 고정값 사용)
LOCK_FILE = "runtime/scheduler.lock"
HEALTH_FILE = "runtime/healthcheck.json"
TERMINATE_FILE = "runtime/terminate.flag"


def is_running():
    """이미 실행 중인 스케줄러인지 확인"""
    return os.path.exists(LOCK_FILE)


def create_lock():
    """실행 잠금 파일 생성"""
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    logger.info("🔒 실행 잠금 파일 생성됨.")


def remove_lock():
    """잠금 파일 제거"""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
        logger.info("🔓 실행 잠금 해제 완료.")


def check_termination():
    """사용자 종료 요청 여부 확인"""
    return os.path.exists(TERMINATE_FILE)


def write_health(status: str = "running"):
    """시스템 상태 기록"""
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)
    data = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": cpu,
        "mem_percent": memory.percent
    }
    save_json(HEALTH_FILE, data)
    logger.debug(f"🩺 상태 기록됨: {data}")
