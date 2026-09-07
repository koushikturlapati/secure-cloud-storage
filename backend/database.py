import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
db_user = os.getenc("DB_USER")
db_password = os.getenv
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenc("DB_NAME")

db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(db_url)
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
