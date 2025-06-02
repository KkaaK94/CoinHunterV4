import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# 명시적으로 .env 경로 지정
dotenv_path = Path(__file__).resolve().parents[2] / 'config' / '.env'
load_dotenv(dotenv_path)

def send_telegram_message(message: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[텔레그램 오류] 환경변수에 TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 누락")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"[텔레그램 전송 실패] {response.text}")
    except Exception as e:
        print(f"[텔레그램 예외] {e}")
