import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from backend.models import Base

load_dotenv()

# MySQL configuration
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT", "3306")
db_name = os.getenv("DB_NAME")

# Validate configuration
if not all((db_user, db_password, db_host, db_name)):
    raise RuntimeError("MySQL database configuration is incomplete.")

# Create MySQL connection URL
database_url = URL.create(
    "mysql+pymysql",
    username=db_user,
    password=db_password,
    host=db_host,
    port=int(db_port),
    database=db_name,
    query={"charset": "utf8mb4"}
)

# Create engine
engine = create_engine(
    database_url,
    pool_pre_ping=True
)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Database session
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