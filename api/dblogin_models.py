from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declartive_base
Base = declarative_base()

class loginModel(Base):

    __tablename_ = "login"
    username = Column(str, unique=True,)
    password = Column(str)