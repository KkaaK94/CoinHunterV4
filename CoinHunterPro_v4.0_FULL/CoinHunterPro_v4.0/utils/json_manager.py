# utils/json_manager.py

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
import shutil
from cryptography.fernet import Fernet

# 환경 변수 로딩
load_dotenv()

# 데이터 경로 설정
DATA_PATH = os.getenv("DATA_PATH", "data_io/json_store")
SECRET_KEY = os.getenv("JSON_SECRET_KEY", Fernet.generate_key().decode())
fernet = Fernet(SECRET_KEY.encode())

# 파일 경로 구성기
def _get_path(filename: str) -> Path:
    return Path(DATA_PATH) / filename

# 안전한 JSON 로드
def load_json(filename: str, default=None):
    path = _get_path(filename)
    if not path.exists():
        logger.warning(f"[load_json] 파일 없음: {path}")
        return default if default is not None else {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"[load_json] 파일 읽기 실패: {path} | 예외: {e}")
        return default if default is not None else {}

# 암호화된 JSON 복호화 로딩
def load_json_secure(filename: str, default=None):
    path = _get_path(filename)
    if not path.exists():
        logger.warning(f"[load_json_secure] 파일 없음: {path}")
        return default if default is not None else {}
    try:
        with open(path, "rb") as f:
            encrypted = f.read()
            decrypted = fernet.decrypt(encrypted).decode()
            return json.loads(decrypted)
    except Exception as e:
        logger.warning(f"[load_json_secure] 복호화 실패: {path} | 예외: {e}")
        return default if default is not None else {}

# 안전한 JSON 저장 (백업 포함)
def save_json(filename: str, data):
    path = _get_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if path.exists():
            shutil.copy(path, str(path) + ".bak")
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"[save_json] 저장 완료: {path}")
    except Exception as e:
        logger.error(f"[save_json] 저장 실패: {path} | 예외: {e}")

# 리스트 형식 JSON에 항목 추가
def append_json_list(filename: str, item: dict):
    data = load_json(filename, default=[])
    if isinstance(data, list):
        data.append(item)
        save_json(filename, data)
    else:
        logger.warning(f"[append_json_list] 기존 형식 오류: {filename} (list 아님)")

# JSON 파일 삭제
def delete_json(filename: str):
    path = _get_path(filename)
    try:
        if path.exists():
            path.unlink()
            logger.info(f"[delete_json] 삭제 완료: {path}")
        else:
            logger.warning(f"[delete_json] 파일 없음: {path}")
    except Exception as e:
        logger.error(f"[delete_json] 삭제 실패: {path} | 예외: {e}")

# JSON 암호화 저장
def save_json_secure(filename: str, data):
    path = _get_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if path.exists():
            shutil.copy(path, str(path) + ".bak")
        raw = json.dumps(data, indent=2, ensure_ascii=False).encode()
        encrypted = fernet.encrypt(raw)
        with open(path, "wb") as f:
            f.write(encrypted)
        logger.info(f"[save_json_secure] 암호화 저장 완료: {path}")
    except Exception as e:
        logger.error(f"[save_json_secure] 저장 실패: {path} | 예외: {e}")
