from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    school = Column(String)
    display_name = Column(String)
    bio = Column(String)
    interests = Column(JSON, default=list)  # เปลี่ยนจาก ARRAY เป็น JSON
    profile_pic = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)