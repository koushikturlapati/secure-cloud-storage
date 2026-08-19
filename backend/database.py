from sqlalchemy import create_engine
from sqlalchemy import sessionmaker


db_url = "mysql+mysqlconnector://root:mysql@localhost:3306/secure_cloud" 
engine = create_engine(db_url)
session =sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = session()
    try:
        yeild db
    finally:
        db.close()