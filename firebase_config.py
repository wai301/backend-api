import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
import os

# Get the current directory
current_dir = Path(__file__).resolve().parent

# Initialize Firebase with service account
try:
    cred = credentials.Certificate(
        current_dir / 'serviceAccountKey.json'
    )
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully!")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    raise

# Collection names (ชื่อ collections ใน Firestore)
USERS_COLLECTION = 'users'
CHATS_COLLECTION = 'chats'
MESSAGES_COLLECTION = 'messages'
SCHOOLS_COLLECTION = 'schools'

def get_firestore_db():
    """Returns the Firestore database instance"""
    return db

# ฟังก์ชันสำหรับจัดการ timestamps
def get_server_timestamp():
    """Returns a server timestamp"""
    return firestore.SERVER_TIMESTAMP