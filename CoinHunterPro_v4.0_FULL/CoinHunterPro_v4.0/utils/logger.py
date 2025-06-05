# utils/logger.py

from loguru import logger
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로딩
load_dotenv()

# 로그 환경 설정
ENV = os.getenv("ENV", "prod")
LOG_DIR = os.getenv("LOG_DIR", "data_io/logs") if ENV != "test" else "data_io/test_logs"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
RETENTION_DAYS = os.getenv("RETENTION_DAYS", "7 days")

Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
today = datetime.now().strftime("%Y%m%d")
LOG_FILE_PATH = os.path.join(LOG_DIR, f"log_{today}.log")
ERROR_LOG_PATH = os.path.join(LOG_DIR, f"error_{today}.log")

# 기존 핸들러 제거
logger.remove()

# 일반 로그 핸들러
logger.add(
    LOG_FILE_PATH,
    rotation="5 MB",
    retention=RETENTION_DAYS,
    encoding="utf-8",
    level=LOG_LEVEL,
    backtrace=True,
    diagnose=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)

# 콘솔 로그 핸들러
logger.add(
    lambda msg: print(msg, end=""),
    level=LOG_LEVEL,
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{function}</cyan> - <level>{message}</level>"
)

# 오류 전용 로그 핸들러
logger.add(
    ERROR_LOG_PATH,
    level="ERROR",
    retention=RETENTION_DAYS,
    rotation="5 MB",
    encoding="utf-8",
    format="<red>{time:YYYY-MM-DD HH:mm:ss}</red> | <level>{level}</level> | {message}"
)
