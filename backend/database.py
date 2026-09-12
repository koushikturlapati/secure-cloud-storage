import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

required_settings = {
    "DB_USER": db_user,
    "DB_PASSWORD": db_password,
    "DB_HOST": db_host,
    "DB_PORT": db_port,
    "DB_NAME": db_name,
}
missing_settings = [name for name, value in required_settings.items() if not value]
if missing_settings:
    raise RuntimeError(
        f"Missing database environment variables: {', '.join(missing_settings)}"
    )

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
