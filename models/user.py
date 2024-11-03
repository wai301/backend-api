from firebase_config import db, USERS_COLLECTION
from datetime import datetime
from .base import FirebaseError, NotFoundError, DuplicateError
from logging_config import logger

class User:
    @staticmethod
    async def create(user_data: dict):
        """Create new user"""
        try:
            doc_ref = db.collection(USERS_COLLECTION).document(user_data['username'])
            
            if doc_ref.get().exists:
                raise DuplicateError("Username already exists")
                
            doc_ref.set({
                'username': user_data['username'],
                'email': user_data['email'],
                'hashed_password': user_data['hashed_password'],
                'school': user_data['school'],
                'display_name': user_data.get('display_name', user_data['username']),
                'bio': user_data.get('bio', ''),
                'interests': user_data.get('interests', []),
                'profile_pic': user_data.get('profile_pic', None),
                'created_at': datetime.utcnow(),
                'last_online': datetime.utcnow(),
                'is_active': True
            })
            return user_data['username']
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise FirebaseError(f"Error creating user: {str(e)}")

    @staticmethod
    async def get_by_username(username: str):
        """Get user by username"""
        try:
            doc = db.collection(USERS_COLLECTION).document(username).get()
            return doc.to_dict() if doc.exists else None
            
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            raise FirebaseError(f"Error getting user: {str(e)}")

    @staticmethod
    async def get_by_email(email: str):
        """Get user by email"""
        try:
            users = db.collection(USERS_COLLECTION).where('email', '==', email).limit(1).get()
            return users[0].to_dict() if users else None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise FirebaseError(f"Error getting user by email: {str(e)}")

    @staticmethod 
    async def update(username: str, update_data: dict):
        """Update user data"""
        try:
            doc_ref = db.collection(USERS_COLLECTION).document(username)
            doc_ref.update(update_data)
            return True
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise FirebaseError(f"Error updating user: {str(e)}")