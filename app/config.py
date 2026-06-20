import os

from sqlalchemy import URL


def _enabled(value):
    return str(value).lower() in {"1", "true", "yes", "on"}


def database_url():
    if configured_url := os.getenv("DATABASE_URL"):
        return configured_url
    return URL.create(
        "mysql+pymysql",
        username=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "rootpass"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3307")),
        database=os.getenv("DB_NAME", "inspection_db"),
        query={"charset": "utf8mb4"},
    )


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "connect_args": {"ssl": {}} if _enabled(os.getenv("DB_SSL", "false")) else {},
    }
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _enabled(os.getenv("SESSION_COOKIE_SECURE", "false"))
