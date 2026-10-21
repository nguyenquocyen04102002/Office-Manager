import os
from datetime import time


def _bool(value: str) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _time(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


class Settings:
    """Đọc cấu hình từ biến môi trường (xem .env.example)."""

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://office_user:office_password@localhost:15432/office_db",
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:18080").split(",")
        if o.strip()
    ]
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh")
    WORK_START: time = _time(os.getenv("WORK_START", "08:30"))
    WORK_END: time = _time(os.getenv("WORK_END", "17:30"))
    SEED_DEMO_DATA: bool = _bool(os.getenv("SEED_DEMO_DATA", "true"))
    SEED_ADMIN_EMAIL: str = os.getenv("SEED_ADMIN_EMAIL", "admin@congty.vn")
    SEED_ADMIN_PASSWORD: str = os.getenv("SEED_ADMIN_PASSWORD", "Admin@123")


settings = Settings()
