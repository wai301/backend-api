# utils/chat.py
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException
from logging_config import logger
from models import User, Chat, Message
from firebase_config import db, USERS_COLLECTION, CHATS_COLLECTION
import random

class ChatManager:
    def __init__(self):
        # ไม่จำเป็นต้องเก็บข้อมูลในตัวแปรแล้ว เพราะใช้ Firebase
        pass

    async def update_user_status(self, user_id: str) -> None:
        try:
            await User.update_last_online(user_id, datetime.utcnow())
            logger.info(f"Updated online status for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating user status: {e}")

    async def is_user_online(self, user_id: str) -> bool:
        try:
            user_doc = db.collection(USERS_COLLECTION).document(user_id).get()
            if not user_doc.exists:
                return False
                
            user_data = user_doc.to_dict()
            last_online = user_data.get('last_online')
            if not last_online:
                return False
                
            is_online = (datetime.utcnow() - last_online) < timedelta(minutes=5)
            logger.info(f"User {user_id} online status: {is_online}")
            return is_online
            
        except Exception as e:
            logger.error(f"Error checking online status: {e}")
            return False

    async def get_waiting_status(self, user_id: str) -> Optional[Dict]:
        try:
            # เช็คในคิวรอ
            waiting_doc = db.collection('waiting_users').document(user_id).get()
            if waiting_doc.exists:
                waiting_data = waiting_doc.to_dict()
                return {
                    "status": "waiting",
                    "school": waiting_data['school']
                }
            return None
        except Exception as e:
            logger.error(f"Error getting waiting status: {e}")
            return None

    async def get_active_chat_status(self, user_id: str) -> Optional[Dict]:
        try:
            # หาแชทที่กำลังใช้งาน
            chats = db.collection(CHATS_COLLECTION)\
                .where('status', '==', 'active')\
                .where('users', 'array_contains', user_id)\
                .limit(1)\
                .get()

            if not chats:
                return None

            chat = chats[0]
            chat_data = chat.to_dict()

            # หาคู่สนทนา
            partner_id = chat_data['user2_id'] if user_id == chat_data['user1_id'] else chat_data['user1_id']
            partner = await User.get_by_username(partner_id)

            if not partner:
                return None

            return {
                "status": "in_chat",
                "chat_id": chat.id,
                "partner": {
                    "username": partner['username'],
                    "school": chat_data['school'],
                    "online": await self.is_user_online(partner_id)
                }
            }

        except Exception as e:
            logger.error(f"Error getting active chat status: {e}")
            return None

    async def find_match(self, current_user: Dict, school: str) -> Dict:
        try:
            # เช็คว่าอยู่ในแชทอยู่แล้วหรือไม่
            active_chat = await self.get_active_chat_status(current_user['username'])
            if active_chat:
                raise HTTPException(status_code=400, detail="Already in chat")

            # ลบออกจากคิวรอถ้ามี
            waiting_ref = db.collection('waiting_users').document(current_user['username'])
            if waiting_ref.get().exists:
                waiting_ref.delete()

            # หาคู่จากโรงเรียนเดียวกัน
            waiting_users = db.collection('waiting_users')\
                .where('school', '==', school)\
                .where('username', '!=', current_user['username'])\
                .get()

            available_users = [
                user.to_dict() for user in waiting_users 
                if await self.is_user_online(user.get('username'))
            ]

            if available_users:
                # สุ่มเลือกคู่สนทนา
                partner = random.choice(available_users)
                
                # สร้างห้องแชท
                chat_id = await Chat.create(
                    user1_id=current_user['username'],
                    user2_id=partner['username'],
                    school=school
                )

                # ลบคู่สนทนาออกจากคิวรอ
                db.collection('waiting_users').document(partner['username']).delete()

                return {
                    "status": "matched",
                    "chat_id": chat_id,
                    "partner": {
                        "username": partner['username'],
                        "school": school,
                        "online": True
                    }
                }

            # ถ้าไม่เจอคู่ ใส่เข้าคิวรอ
            waiting_ref.set({
                'username': current_user['username'],
                'school': school,
                'joined_at': datetime.utcnow()
            })
            
            return {"status": "waiting"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error finding match: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def reset(self) -> None:
        try:
            # ลบข้อมูลทั้งหมด
            batch = db.batch()
            
            # ลบคิวรอ
            waiting_refs = db.collection('waiting_users').limit(500).get()
            for ref in waiting_refs:
                batch.delete(ref.reference)
            
            # ลบแชทที่ active
            chat_refs = db.collection(CHATS_COLLECTION).where('status', '==', 'active').limit(500).get()
            for ref in chat_refs:
                batch.delete(ref.reference)
            
            # ดำเนินการลบ
            batch.commit()
            logger.info("Reset chat system completed")
            
        except Exception as e:
            logger.error(f"Error resetting chat system: {e}")
            raise HTTPException(status_code=400, detail=str(e))

# สร้าง instance เดียวใช้ทั้งระบบ
chat_manager = ChatManager()