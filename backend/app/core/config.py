import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    # -------------------------
    # Environment
    # -------------------------
    ENV = os.getenv("ENV", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # -------------------------
    # Application
    # -------------------------
    APP_NAME = os.getenv("APP_NAME", "laundry-management-system")
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 80))
    APP_DOMAIN = os.getenv("APP_DOMAIN", "localhost")

    # -------------------------
    # Database
    # -------------------------
    # Auto-convert postgresql:// → postgresql+psycopg:// for psycopg3 driver
    _db_url = os.getenv("DATABASE_URL", "")
    if _db_url.startswith("postgresql://"):
        _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url or None
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis — Phase 2 only (job queues, caching). Not needed in Phase 1.
    # REDIS_URL = os.getenv("REDIS_URL")

    # -------------------------
    # Security
    # -------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "laundry-secret-change-in-prod")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "laundry-jwt-secret-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = 28800  # 8 hours in seconds

    # -------------------------
    # Logging
    # -------------------------
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
