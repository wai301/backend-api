from firebase_config import db, MESSAGES_COLLECTION
from datetime import datetime
from .base import FirebaseError
from logging_config import logger

class Message:
    @staticmethod
    async def create(message_data: dict):
        """Create new message"""
        try:
            message_ref = db.collection(MESSAGES_COLLECTION).document()
            message_data['created_at'] = datetime.utcnow()
            message_ref.set(message_data)
            return message_ref.id
            
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            raise FirebaseError(str(e))

    @staticmethod
    async def get_chat_messages(chat_id: str, limit: int = 50):
        """Get messages for chat"""
        try:
            messages = []
            query = (db.collection(MESSAGES_COLLECTION)
                    .where('chat_id', '==', chat_id)
                    .order_by('created_at', direction='desc')
                    .limit(limit))
                    
            for doc in query.stream():
                message = doc.to_dict()
                message['id'] = doc.id
                messages.append(message)
                
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            raise FirebaseError(str(e))