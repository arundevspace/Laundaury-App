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
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------
    # Redis
    # -------------------------
    REDIS_URL = os.getenv("REDIS_URL")

    # -------------------------
    # Security
    # -------------------------
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    # -------------------------
    # Logging
    # -------------------------
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
