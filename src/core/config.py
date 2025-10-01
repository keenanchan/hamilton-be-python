import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    APP_NAME = "hamilton-be"
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV == "development"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/hamilton")
    ACCESS_TOKEN_EXPIRES_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRES_MIN", 60))

config = Config()