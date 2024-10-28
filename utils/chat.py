from datetime import datetime, timedelta
from typing import Dict, List

# เก็บข้อมูลผู้ใช้ที่กำลังรอแชท
waiting_users: List[Dict] = []

# เก็บข้อมูลห้องแชท
active_chats: Dict = {}

# เก็บข้อมูลผู้ใช้ที่ออนไลน์
online_users: Dict[int, datetime] = {}

def update_user_status(user_id: int):
    """อัพเดทสถานะออนไลน์ของผู้ใช้"""
    online_users[user_id] = datetime.now()

def is_user_online(user_id: int) -> bool:
    """เช็คว่าผู้ใช้ออนไลน์อยู่หรือไม่"""
    if user_id not in online_users:
        return False
    return datetime.now() - online_users[user_id] < timedelta(minutes=5)

def get_chat_partner(chat_id: str, current_user_id: int):
    """หาคู่สนทนาในห้องแชท"""
    if chat_id not in active_chats:
        return None
    
    chat = active_chats[chat_id]
    return chat['user2'] if current_user_id == chat['user1'].id else chat['user1']

def format_message(content: str, sender_id: int, sender_username: str):
    """สร้างรูปแบบข้อความ"""
    return {
        'content': content,
        'sender_id': sender_id,
        'sender_username': sender_username,
        'timestamp': datetime.now().isoformat()
    }

def cleanup_inactive_chats():
    """ลบห้องแชทที่ไม่มีการใช้งาน"""
    now = datetime.now()
    inactive_chats = []
    
    for chat_id, chat in active_chats.items():
        if not is_user_online(chat['user1'].id) and not is_user_online(chat['user2'].id):
            inactive_chats.append(chat_id)
    
    for chat_id in inactive_chats:
        del active_chats[chat_id]