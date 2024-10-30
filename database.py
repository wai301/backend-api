from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import time
import logging

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ใช้ DATABASE_URL จาก environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
logger.info(f"Initial DATABASE_URL: {DATABASE_URL}")

# ฟังก์ชันสำหรับสร้าง engine พร้อม retry
def create_db_engine(url, max_retries=5):
    for attempt in range(max_retries):
        try:
            if "postgres.railway.internal" in url:
                url = url.replace(
                    "postgres.railway.internal",
                    "monorail.proxy.rlwy.net"
                )
            logger.info(f"Attempt {attempt + 1}: Connecting to {url}")
            
            # เพิ่ม connect_args สำหรับ timeout
            engine = create_engine(
                url,
                connect_args={
                    "connect_timeout": 10,
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5
                }
            )
            
            # ทดสอบการเชื่อมต่อ
            with engine.connect() as conn:
                conn.execute("SELECT 1")  # ทดสอบ connection จริงๆ
            logger.info("Database connection successful!")
            return engine
            
        except Exception as e:
            logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.warning("All connection attempts failed, falling back to SQLite")
                sqlite_url = "sqlite:///./sql_app.db"
                return create_engine(
                    sqlite_url, 
                    connect_args={"check_same_thread": False}
                )

# สร้าง engine
if not DATABASE_URL:
    logger.warning("No DATABASE_URL found, using SQLite")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    # แก้ไข postgres:// เป็น postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        logger.info("Modified URL to use postgresql:// scheme")
    
    engine = create_db_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()