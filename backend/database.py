from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


db_url = "mysql+pymysql://root:mysql@127.0.0.1:3306/secure_cloud"
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
