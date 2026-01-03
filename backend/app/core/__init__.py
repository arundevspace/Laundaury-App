import os

class Config:
    ENV = os.getenv("ENV", "dev")
    DEBUG = ENV == "dev"

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/laundry_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
