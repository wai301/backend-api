from firebase_config import db, CHATS_COLLECTION
from datetime import datetime
from .base import FirebaseError, NotFoundError
from logging_config import logger

class Chat:
    @staticmethod
    async def create(user1_id: str, user2_id: str, school: str):
        """Create new chat"""
        try:
            chat_ref = db.collection(CHATS_COLLECTION).document()
            chat_ref.set({
                'user1_id': user1_id,
                'user2_id': user2_id,
                'school': school,
                'status': 'active',
                'created_at': datetime.utcnow(),
                'last_activity': datetime.utcnow()
            })
            return chat_ref.id
            
        except Exception as e:
            logger.error(f"Error creating chat: {e}")
            raise FirebaseError(str(e))

    @staticmethod
    async def get_chat(chat_id: str):
        """Get chat by ID"""
        try:
            doc = db.collection(CHATS_COLLECTION).document(chat_id).get()
            return doc.to_dict() if doc.exists else None
            
        except Exception as e:
            logger.error(f"Error getting chat: {e}")
            raise FirebaseError(str(e))