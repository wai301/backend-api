import logging
from firebase_admin import firestore
from firebase_config import db

# ตั้งค่า logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_db():
    """
    Initialize Firebase connection
    Returns Firebase db instance if successful
    """
    try:
        logger.info("Starting Firebase initialization...")
        
        # Test connection by writing to a test collection
        test_ref = db.collection('system').document('connection_test')
        test_ref.set({
            'status': 'connected',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'environment': 'production'
        })
        
        logger.info("✅ Firebase initialized successfully!")
        return db
        
    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {str(e)}")
        raise

def get_db():
    """
    Database dependency injection for FastAPI
    Returns Firebase db instance
    """
    try:
        return db
    except Exception as e:
        logger.error(f"Error accessing Firebase instance: {str(e)}")
        raise

def test_db_connection():
    """
    Test database connection on startup
    Raises exception if connection fails
    """
    try:
        # Write test document
        test_ref = db.collection('system').document('startup_test')
        test_ref.set({
            'status': 'online',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'message': 'System startup test successful'
        })
        
        # Read test document
        test_doc = test_ref.get()
        if test_doc.exists:
            logger.info("✅ Database connection test passed")
        else:
            raise Exception("Test document not found")
            
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {str(e)}")
        raise

# Initialize database on module import
try:
    db = initialize_db()
    test_db_connection()
except Exception as e:
    logger.critical(f"❌ FATAL: Database initialization failed: {str(e)}")
    raise

# Export database instance
firebase_db = db