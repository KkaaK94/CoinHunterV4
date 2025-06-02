# services/cli/realtime_paper_trader.py

import time
import os
import json
import pandas as pd
import pyupbit
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime
from strategies.seed_160k import Seed160kStrategy
from pathlib import Path
from app_core.infra_control.push_notification import send_telegram_message



POSITION_FILE = "data_io/json_store/position_log.json"
TICKER = "KRW-BTC"
INTERVAL = "minute1"
STRATEGY = Seed160kStrategy()


def fetch_latest_candles(ticker=TICKER, count=100):
    df = pyupbit.get_ohlcv(ticker, interval=INTERVAL, count=count)
    df.reset_index(inplace=True)
    df.rename(columns={"index": "date"}, inplace=True)
    return df


def calculate_macd(df):
    df['ema_short'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema_long'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema_short'] - df['ema_long']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    return df


def fetch_dummy_fgi(fgi_value=20):
    # 실시간 FGI가 없기 때문에 고정값 (또는 외부 API 연동 확장 가능)
    return fgi_value


def load_position():
    if os.path.exists(POSITION_FILE):
        try:
            with open(POSITION_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    return None


def save_position(position):
    Path(os.path.dirname(POSITION_FILE)).mkdir(parents=True, exist_ok=True)
    with open(POSITION_FILE, 'w') as f:
        json.dump(position, f, indent=2, default=str)


def run_once():
    df = fetch_latest_candles()
    df = calculate_macd(df)
    fgi = fetch_dummy_fgi()
    df['fgi'] = fgi

    df = STRATEGY.generate_signals(df)
    latest = df.iloc[-1]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    position = load_position()

    if latest['buy'] and not position:
        entry_price = latest['close']
        position = {
            "entry_time": now,
            "entry_price": entry_price,
            "amount": round(STRATEGY.position_size / entry_price, 6),
            "status": "HOLD"
        }
        save_position(position)
        print(f"[매수] {now} 진입가: {entry_price:,.0f}원")
        send_telegram_message(f"[📈 {STRATEGY.name()}] 매수 진입\n가격: {entry_price:.2f}₩")

    elif position and latest['sell']:
        exit_price = latest['close']
        entry_price = position['entry_price']
        amount = position['amount']
        pnl_amount = (exit_price - entry_price) * amount
        pnl_pct = (exit_price - entry_price) / entry_price * 100

        print(f"[청산] {now} 청산가: {exit_price:,.0f}원 / 수익: {pnl_amount:,.0f}원 ({pnl_pct:.2f}%)")
        send_telegram_message(
            f"[💰 {STRATEGY.name()}] 청산 완료\n가격: {exit_price:.2f}₩\n수익: {pnl_amount:,.0f}₩\n수익률: {pnl_pct:.2f}%"
        )
        save_position(None)  # 청산 후 포지션 제거

    elif position:
        # 실시간 수익률 출력
        current_price = latest['close']
        pnl = (current_price - position['entry_price']) * position['amount']
        print(f"[유지] {now} 현재가: {current_price:,.0f}원 / PnL: {pnl:,.0f}원")


if __name__ == "__main__":
    while True:
        try:
            run_once()
            time.sleep(60)
        except KeyboardInterrupt:
            print("\n[종료] 수동 중단됨")
            break
        except Exception as e:
            print(f"[오류] {e}")
            time.sleep(10)
