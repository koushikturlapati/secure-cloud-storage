from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True,index=True)
    username =Column(String(50), unique=True, nullable=False)
    password_hash=Column(String(255),nullable=False)
    created_at=Column(TIMESTAMP, server_default=func.now())