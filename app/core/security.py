import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from jose import jwt, JWTError
from passlib.context import CryptContext

load_dotenv()

logger = logging.getLogger(__name__)

_secret = os.getenv("SECRET_KEY")
_env = os.getenv("DAYFLOW_ENV", "").lower()
_is_dev_mode = (
    _env in ("dev", "development")
    or os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
    or os.getenv("DEV", "").lower() in ("true", "1", "yes")
)

if not _secret:
    if _is_dev_mode:
        logger.warning("WARNING: SECRET_KEY is not set. Using dev-only default secret key because dev mode is enabled.")
        SECRET_KEY = "dev_only_default_secret_key_do_not_use_in_production"
    else:
        raise RuntimeError(
            "FATAL SECURITY CONFIGURATION ERROR: SECRET_KEY environment variable is not set. "
            "Please define SECRET_KEY in your .env file or environment, or set DAYFLOW_ENV=dev for local development."
        )
else:
    SECRET_KEY = _secret

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}
