from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ใช้ DATABASE_URL จาก environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

print(f"Original DATABASE_URL: {DATABASE_URL}")  # เพิ่ม log

# ถ้าไม่มี DATABASE_URL ใช้ SQLite แทน
if not DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # แก้ไข postgres:// เป็น postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # แก้ไข internal hostname
    if "postgres.railway.internal" in DATABASE_URL:
        # แก้เป็น public hostname
        DATABASE_URL = DATABASE_URL.replace(
            "postgres.railway.internal",
            "monorail.proxy.rlwy.net"
        )
    
    print(f"Modified DATABASE_URL: {DATABASE_URL}")  # เพิ่ม log
    
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()