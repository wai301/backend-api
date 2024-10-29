from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import time

# ใช้ DATABASE_URL จาก environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

print(f"Original DATABASE_URL: {DATABASE_URL}")

# ฟังก์ชันสำหรับสร้าง engine พร้อม retry
def create_db_engine(url, max_retries=5):
    for attempt in range(max_retries):
        try:
            if "postgres.railway.internal" in url:
                url = url.replace(
                    "postgres.railway.internal",
                    "monorail.proxy.rlwy.net"
                )
            print(f"Attempt {attempt + 1}: Connecting to {url}")
            engine = create_engine(url)
            # ทดสอบการเชื่อมต่อ
            with engine.connect() as conn:
                pass
            return engine
        except Exception as e:
            print(f"Connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # exponential backoff
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("All connection attempts failed, falling back to SQLite")
                sqlite_url = "sqlite:///./sql_app.db"
                return create_engine(sqlite_url, connect_args={"check_same_thread": False})

# สร้าง engine
if not DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # แก้ไข postgres:// เป็น postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_db_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()