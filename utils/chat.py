from datetime import datetime, timedelta 
import random 
from typing import Dict, List, Optional 
from fastapi import HTTPException 
from logging_config import logger

class ChatManager:
    def __init__(self):
        self.waiting_users: List[Dict] = []
        self.active_chats: Dict = {}
        self.online_users: Dict[int, datetime] = {}

    def update_user_status(self, user_id: int) -> None:
        self.online_users[user_id] = datetime.now()
        logger.info(f"Updated online status for user {user_id}")

    def is_user_online(self, user_id: int) -> bool:
        if user_id not in self.online_users:
            return False
        is_online = datetime.now() - self.online_users[user_id] < timedelta(minutes=5)
        logger.info(f"User {user_id} online status: {is_online}")
        return is_online

    def get_chat(self, chat_id: str) -> Optional[Dict]:
        return self.active_chats.get(chat_id)

    def add_message(self, chat_id: str, message: Dict) -> None:
        if chat_id in self.active_chats:
            self.active_chats[chat_id]['messages'].append(message)

    def remove_chat(self, chat_id: str) -> None:
        if chat_id in self.active_chats:
            del self.active_chats[chat_id]

    def get_waiting_status(self, user_id: int) -> Optional[Dict]:
        for user in self.waiting_users:
            if user['user'].id == user_id:
                return {"status": "waiting", "school": user['school']}
        return None

    def get_active_chat_status(self, user_id: int) -> Optional[Dict]:
        for chat_id, chat in self.active_chats.items():
            if user_id in [chat['user1'].id, chat['user2'].id]:
                partner = chat['user2'] if user_id == chat['user1'].id else chat['user1']
                return {
                    "status": "in_chat",
                    "chat_id": chat_id,
                    "partner": {
                        "username": partner.username,
                        "school": chat['school'],
                        "online": self.is_user_online(partner.id)
                    }
                }
        return None

    def find_match(self, current_user, school: str) -> Dict:
        # Check if user is already in chat
        for chat_id, chat in self.active_chats.items():
            if current_user.id in [chat['user1'].id, chat['user2'].id]:
                raise HTTPException(status_code=400, detail="Already in chat")

        # Remove from waiting list if exists
        self.waiting_users[:] = [u for u in self.waiting_users if u['user'].id != current_user.id]

        # Find match from same school
        available_users = [
            u for u in self.waiting_users 
            if u['school'] == school and 
            u['user'].id != current_user.id and 
            self.is_user_online(u['user'].id)
        ]

        if available_users:
            waiting_user = random.choice(available_users)
            chat_id = f"{current_user.id}-{waiting_user['user'].id}"
            
            self.active_chats[chat_id] = {
                'user1': current_user,
                'user2': waiting_user['user'],
                'school': school,
                'messages': [],
                'started_at': datetime.now()
            }
            self.waiting_users.remove(waiting_user)
            
            return {
                "status": "matched",
                "chat_id": chat_id,
                "partner": {
                    "username": waiting_user['user'].username,
                    "school": school,
                    "online": True
                }
            }

        self.waiting_users.append({
            'user': current_user,
            'school': school
        })
        return {"status": "waiting"}

    def reset(self) -> None:
        self.waiting_users.clear()
        self.active_chats.clear()

# สร้าง instance ของ ChatManager
chat_manager = ChatManager()