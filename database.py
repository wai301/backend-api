from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import os
import time
import logging
from urllib.parse import urlparse

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ใช้ DATABASE_URL จาก environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
logger.info(f"Initial DATABASE_URL: {DATABASE_URL}")

def validate_db_url(url):
    """ตรวจสอบและแก้ไข URL ให้ถูกต้อง"""
    if not url:
        return None
        
    # แก้ไข scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        logger.info("Modified URL to use postgresql:// scheme")
    
    # แก้ไข host
    if "postgres.railway.internal" in url:
        url = url.replace(
            "postgres.railway.internal",
            "monorail.proxy.rlwy.net"
        )
        logger.info("Modified internal host to proxy host")
    
    # ตรวจสอบรูปแบบ URL
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            logger.error("Invalid database URL format")
            return None
    except Exception as e:
        logger.error(f"Error parsing database URL: {e}")
        return None
        
    return url

def create_db_engine(url, max_retries=5):
    """สร้าง database engine พร้อม retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}: Connecting to database...")
            
            # ปรับการตั้งค่า engine
            engine = create_engine(
                url,
                pool_pre_ping=True,
                pool_timeout=30,
                pool_size=5,
                max_overflow=10,
                connect_args={
                    "connect_timeout": 30,
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5
                }
            )
            
            # ทดสอบการเชื่อมต่อ
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.execute(text("SET TIME ZONE 'Asia/Bangkok'"))
            logger.info("Database connection successful!")
            return engine
            
        except OperationalError as e:
            logger.error(f"Operational error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 30)  # Max wait 30 seconds
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error on attempt {attempt + 1}: {str(e)}")
            break
            
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            break
    
    # Fallback to SQLite
    logger.warning("Falling back to SQLite database")
    sqlite_url = "sqlite:///./sql_app.db"
    return create_engine(
        sqlite_url, 
        connect_args={"check_same_thread": False}
    )

# Initialize database connection
try:
    # Validate and correct DATABASE_URL
    valid_url = validate_db_url(DATABASE_URL)
    
    if valid_url:
        engine = create_db_engine(valid_url)
        logger.info("Using PostgreSQL database")
    else:
        # Fallback to SQLite if no valid URL
        logger.warning("No valid DATABASE_URL found, using SQLite")
        engine = create_engine(
            "sqlite:///./sql_app.db",
            connect_args={"check_same_thread": False}
        )
        
    # Test connection one last time
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    
except Exception as e:
    logger.error(f"Fatal error initializing database: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()

# Create test connection on startup
def test_db_connection():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        logger.info("Initial database connection test successful")
    except Exception as e:
        logger.error(f"Initial database connection test failed: {e}")
        raise
    finally:
        db.close()

# Run test connection
test_db_connection()