# models/base.py
import logging
from logging_config import logger
from firebase_config import get_firestore_db, USERS_COLLECTION, CHATS_COLLECTION, MESSAGES_COLLECTION
from firebase_admin import firestore
from datetime import datetime
from typing import Optional, List, Dict, Any

db = get_firestore_db()

# Custom Exceptions
class FirebaseError(Exception):
   pass

class NotFoundError(FirebaseError):
   pass
   
class DuplicateError(FirebaseError):
   pass

# Base Model
class BaseModel:
   @staticmethod
   def validate_data(data: Dict[str, Any]) -> None:
       """Validate data before database operations"""
       if not isinstance(data, dict):
           raise ValueError("Data must be a dictionary")

# models/user.py
class User(BaseModel):
   def __init__(
       self, 
       username: str, 
       email: str, 
       hashed_password: str,
       school: str,
       display_name: Optional[str] = None,
       bio: Optional[str] = None,
       interests: Optional[List[str]] = None,
       profile_pic: Optional[str] = None,
       is_active: bool = True
   ):
       self.username = username
       self.email = email
       self.hashed_password = hashed_password
       self.school = school
       self.display_name = display_name or username
       self.bio = bio
       self.interests = interests or []
       self.profile_pic = profile_pic
       self.created_at = datetime.utcnow()
       self.is_active = is_active

   @staticmethod
   async def create(user_data: Dict[str, Any]) -> str:
       """Create new user"""
       try:
           # Validate input
           BaseModel.validate_data(user_data)
           
           doc_ref = db.collection(USERS_COLLECTION).document(user_data['username'])
           
           # Check username
           if doc_ref.get().exists:
               logger.error(f"Username already exists: {user_data['username']}")
               raise DuplicateError("Username already exists")
           
           # Check email
           email_query = db.collection(USERS_COLLECTION).where('email', '==', user_data['email']).limit(1).get()
           if len(email_query) > 0:
               logger.error(f"Email already registered: {user_data['email']}")
               raise DuplicateError("Email already registered")

           # Prepare user data
           user_dict = {
               'username': user_data['username'],
               'email': user_data['email'],
               'hashed_password': user_data['hashed_password'],
               'school': user_data['school'],
               'display_name': user_data.get('display_name', user_data['username']),
               'bio': user_data.get('bio', ''),
               'interests': user_data.get('interests', []),
               'profile_pic': user_data.get('profile_pic', None),
               'created_at': firestore.SERVER_TIMESTAMP,
               'is_active': True,
               'last_online': firestore.SERVER_TIMESTAMP
           }
           
           # Create user
           doc_ref.set(user_dict)
           logger.info(f"Created user: {user_data['username']}")
           return user_data['username']

       except FirebaseError:
           raise
       except Exception as e:
           logger.error(f"Error creating user: {e}")
           raise FirebaseError(f"Error creating user: {str(e)}")

   @staticmethod
   async def get_by_username(username: str) -> Optional[Dict[str, Any]]:
       """Get user by username"""
       try:
           doc = db.collection(USERS_COLLECTION).document(username).get()
           if not doc.exists:
               return None
           user_data = doc.to_dict()
           user_data['id'] = doc.id
           return user_data
       except Exception as e:
           logger.error(f"Error getting user: {e}")
           raise FirebaseError(f"Error getting user: {str(e)}")

   @staticmethod
   async def get_by_email(email: str) -> Optional[Dict[str, Any]]:
       """Get user by email"""
       try:
           query = db.collection(USERS_COLLECTION).where('email', '==', email).limit(1).get()
           if not query:
               return None
           user_data = query[0].to_dict()
           user_data['id'] = query[0].id
           return user_data
       except Exception as e:
           logger.error(f"Error getting user by email: {e}")
           raise FirebaseError(f"Error getting user by email: {str(e)}")

   @staticmethod
   async def update(username: str, update_data: Dict[str, Any]) -> bool:
       """Update user data"""
       try:
           BaseModel.validate_data(update_data)
           
           doc_ref = db.collection(USERS_COLLECTION).document(username)
           if not doc_ref.get().exists:
               raise NotFoundError("User not found")

           # Remove protected fields
           protected_fields = ['username', 'email', 'created_at', 'hashed_password']
           for field in protected_fields:
               update_data.pop(field, None)

           # Update
           doc_ref.update(update_data)
           logger.info(f"Updated user: {username}")
           return True

       except FirebaseError:
           raise
       except Exception as e:
           logger.error(f"Error updating user: {e}")
           raise FirebaseError(f"Error updating user: {str(e)}")

   @staticmethod
   async def deactivate(username: str) -> bool:
       """Deactivate user account"""
       try:
           doc_ref = db.collection(USERS_COLLECTION).document(username)
           if not doc_ref.get().exists:
               raise NotFoundError("User not found")
               
           doc_ref.update({
               'is_active': False,
               'deactivated_at': firestore.SERVER_TIMESTAMP
           })
           logger.info(f"Deactivated user: {username}")
           return True
           
       except Exception as e:
           logger.error(f"Error deactivating user: {e}")
           raise FirebaseError(f"Error deactivating user: {str(e)}")

   @staticmethod
   async def search_by_school(school: str) -> List[Dict[str, Any]]:
       """Search users by school"""
       try:
           users = []
           query = db.collection(USERS_COLLECTION).where('school', '==', school).where('is_active', '==', True).get()
           
           for doc in query:
               user_data = doc.to_dict()
               user_data['id'] = doc.id
               users.append(user_data)
               
           return users
           
       except Exception as e:
           logger.error(f"Error searching users by school: {e}")
           raise FirebaseError(f"Error searching users: {str(e)}")

# models/chat.py            
class Chat(BaseModel):
   @staticmethod
   async def create(user1_id: str, user2_id: str, school: str) -> str:
       """Create new chat"""
       try:
           chat_ref = db.collection(CHATS_COLLECTION).document()
           chat_data = {
               'user1_id': user1_id,
               'user2_id': user2_id,
               'school': school,
               'started_at': firestore.SERVER_TIMESTAMP,
               'last_message_at': firestore.SERVER_TIMESTAMP,
               'status': 'active'
           }
           chat_ref.set(chat_data)
           logger.info(f"Created chat between {user1_id} and {user2_id}")
           return chat_ref.id
           
       except Exception as e:
           logger.error(f"Error creating chat: {e}")
           raise FirebaseError(f"Error creating chat: {str(e)}")

   @staticmethod
   async def get_chat(chat_id: str) -> Optional[Dict[str, Any]]:
       """Get chat data"""
       try:
           doc = db.collection(CHATS_COLLECTION).document(chat_id).get()
           if not doc.exists:
               return None
           chat_data = doc.to_dict()
           chat_data['id'] = doc.id
           return chat_data
           
       except Exception as e:
           logger.error(f"Error getting chat: {e}")
           raise FirebaseError(f"Error getting chat: {str(e)}")

   @staticmethod
   async def end_chat(chat_id: str) -> bool:
       """End chat session"""
       try:
           doc_ref = db.collection(CHATS_COLLECTION).document(chat_id)
           if not doc_ref.get().exists:
               raise NotFoundError("Chat not found")
               
           doc_ref.update({
               'status': 'ended',
               'ended_at': firestore.SERVER_TIMESTAMP
           })
           logger.info(f"Ended chat: {chat_id}")
           return True
           
       except Exception as e:
           logger.error(f"Error ending chat: {e}")
           raise FirebaseError(f"Error ending chat: {str(e)}")

# models/message.py
class Message(BaseModel):
   @staticmethod
   async def create(message_data: Dict[str, Any]) -> str:
       """Create new message"""
       try:
           BaseModel.validate_data(message_data)
           
           message_ref = db.collection(MESSAGES_COLLECTION).document()
           message_data['created_at'] = firestore.SERVER_TIMESTAMP
           
           message_ref.set(message_data)
           logger.info(f"Created message in chat: {message_data.get('chat_id')}")
           return message_ref.id
           
       except Exception as e:
           logger.error(f"Error creating message: {e}")
           raise FirebaseError(f"Error creating message: {str(e)}")

   @staticmethod
   async def get_chat_messages(chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
       """Get chat messages"""
       try:
           messages = []
           query = (db.collection(MESSAGES_COLLECTION)
                   .where('chat_id', '==', chat_id)
                   .order_by('created_at', direction='desc')
                   .limit(limit))
           
           docs = query.get()
           for doc in docs:
               message = doc.to_dict()
               message['id'] = doc.id
               messages.append(message)
               
           return messages
           
       except Exception as e:
           logger.error(f"Error getting messages: {e}")
           raise FirebaseError(f"Error getting messages: {str(e)}")