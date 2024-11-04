import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# Collection names
USERS_COLLECTION = 'users'
CHATS_COLLECTION = 'chats'
MESSAGES_COLLECTION = 'messages'
SCHOOLS_COLLECTION = 'schools'

def initialize_firebase():
    try:
        # ลองใช้ environment variable ก่อน
        if 'FIREBASE_CREDENTIALS' in os.environ:
            print("Using environment credentials...")
            cred_dict = json.loads(os.environ['FIREBASE_CREDENTIALS'])
            cred = credentials.Certificate(cred_dict)
        else:
            print("Using local credentials file...")
            cred = credentials.Certificate('serviceAccountKey.json')

        # Initialize Firebase
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"Firebase initialization error: {e}")
        raise

# Initialize Firebase and get db instance
db = initialize_firebase()
print("Firebase initialized successfully!")

def get_firestore_db():
    """Returns the Firestore database instance"""
    return db

def get_server_timestamp():
    """Returns a server timestamp"""
    return firestore.SERVER_TIMESTAMP