# infra_control/push_notification.py

import os
import asyncio
import requests
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# 환경변수 로딩
TELEGRAM_ENABLED = os.getenv("ENABLE_ALERTS", "false").lower() == "true"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

TELEGRAM_LIMIT = 4096

# 텔레그램 알림 (비동기)
async def send_telegram_async(message):
    if not TELEGRAM_ENABLED or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        if len(message) > TELEGRAM_LIMIT:
            message = message[:TELEGRAM_LIMIT - 3] + "..."
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        res = requests.post(url, data=data)
        if res.status_code != 200:
            logger.warning(f"[Telegram] 실패: {res.text}")
    except Exception as e:
        logger.error(f"[Telegram] 예외 발생: {e}")

# 이메일 알림 (비동기)
async def send_email_async(subject, body):
    if not EMAIL_ENABLED or not EMAIL_ADDRESS or not EMAIL_RECEIVER:
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = EMAIL_RECEIVER
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        logger.error(f"[Email] 예외 발생: {e}")

# 템플릿 메시지
ALERT_TEMPLATES = {
    "CRITICAL": "\ud83d\udea8 [CRITICAL] {message}",
    "WARNING": "\u26a0\ufe0f [WARNING] {message}",
    "INFO": "\ud83d\udd14 [INFO] {message}"
}

# 통합 인터페이스 (레벨 구분, 병렬 전송)
def push_alert(message, subject="\ud83d\udd14 \uc804\ub7b5 \uc54c\ub9bc", level="INFO"):
    template = ALERT_TEMPLATES.get(level.upper(), "[ALERT] {message}")
    final_message = template.format(message=message)
    asyncio.run(asyncio.gather(
        send_telegram_async(final_message),
        send_email_async(subject, final_message)
    ))