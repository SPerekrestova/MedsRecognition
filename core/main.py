import os

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from starlette.middleware.sessions import SessionMiddleware

from app_entry import AppEntry


def load_db():
    # Load environment variables from .env
    load_dotenv()

    # Fetch variables
    USER = os.getenv("DATABASE_USER")
    PASSWORD = os.getenv("DATABASE_PASSWORD")
    HOST = os.getenv("DATABASE_HOST")
    PORT = os.getenv("DATABASE_PORT")
    DBNAME = os.getenv("DATABASE_NAME")

    DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
    engine = create_engine(DATABASE_URL, poolclass=NullPool)

    # Test the connection
    try:
        with engine.connect():
            print("DB connection established successfully!")
    except Exception as e:
        print(f"Failed to connect to DB: {e}")


app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key="very-secret-key",
    max_age=86400,  # 1 day
    https_only=True,
    same_site="lax",
)
load_db()
entry_point = AppEntry(app=app)
