import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if not database_url:
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    if all((db_user, db_password, db_host, db_port, db_name)):
        database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        database_path = Path(
            os.getenv(
                "SQLITE_PATH",
                Path(__file__).resolve().parents[1] / "database" / "app.db",
            )
        )
        database_path.parent.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite:///{database_path}"

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, connect_args=connect_args)
if database_url.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
