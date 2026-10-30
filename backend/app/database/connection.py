import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import DATABASE_URL


def get_engine():
    # Attempt connecting to primary DATABASE_URL (e.g. PostgreSQL)
    if DATABASE_URL and ("postgresql" in DATABASE_URL or "postgres" in DATABASE_URL):
        try:
            eng = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 3}
            )
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            return eng
        except Exception as e:
            print(f"Primary PostgreSQL unavailable ({e}). Initializing resilient SQLite database.")

    elif DATABASE_URL and "sqlite" in DATABASE_URL:
        return create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

    # Resilient fallback for serverless cloud environments (such as Vercel)
    fallback_path = "/tmp/interview_simulator.db" if os.name != "nt" else os.path.join(os.path.dirname(__file__), "fallback.db")
    return create_engine(f"sqlite:///{fallback_path}", connect_args={"check_same_thread": False})


engine = get_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
