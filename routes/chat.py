from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from utils.auth import get_current_user
from utils.chat import chat_manager
import models, schemas
from logging_config import logger

router = APIRouter()

from pydantic import BaseModel

class ChatStart(BaseModel):
    school: str

@router.post("/start-chat")
async def start_chat(
    data: ChatStart,
    current_user: models.User = Depends(get_current_user)
):
    logger.info(f"Starting chat for {current_user.username} from {data.school}")
    chat_manager.update_user_status(current_user.id)
    return chat_manager.find_match(current_user, data.school)

@router.post("/send-message/{chat_id}")
async def send_message(
    chat_id: str,
    message: schemas.ChatMessage,
    current_user: models.User = Depends(get_current_user)
):
    chat_manager.update_user_status(current_user.id)
    
    chat = chat_manager.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user1 = chat.get('user1', {})
    user2 = chat.get('user2', {})
    
    if current_user.id not in [user1.get('id'), user2.get('id')]:
        raise HTTPException(status_code=403, detail="You are not in this chat")

    partner = user2 if current_user.id == user1.get('id') else user1
    if not chat_manager.is_user_online(partner.get('id')):
        raise HTTPException(status_code=400, detail="Partner is offline")

    new_message = {
        'content': message.content,
        'sender_id': current_user.id,
        'sender_username': current_user.username,
        'timestamp': datetime.now().isoformat()
    }
    
    chat_manager.add_message(chat_id, new_message)
    logger.info(f"Message sent in chat {chat_id}")
    
    return {
        "status": "sent",
        "message": new_message
    }

@router.get("/chat-messages/{chat_id}")
async def get_messages(
    chat_id: str,
    current_user: models.User = Depends(get_current_user)
):
    chat_manager.update_user_status(current_user.id)

    chat = chat_manager.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user1 = chat.get('user1', {})
    user2 = chat.get('user2', {})
    
    if current_user.id not in [user1.get('id'), user2.get('id')]:
        raise HTTPException(status_code=403, detail="You are not in this chat")

    partner = user2 if current_user.id == user1.get('id') else user1
    partner_online = chat_manager.is_user_online(partner.get('id'))

    return {
        "messages": chat.get('messages', []),
        "partner": {
            "username": partner.get('username'),
            "school": chat.get('school'),
            "online": partner_online
        }
    }

@router.post("/leave-chat/{chat_id}")
async def leave_chat(
    chat_id: str,
    current_user: models.User = Depends(get_current_user)
):
    chat = chat_manager.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user1 = chat.get('user1', {})
    user2 = chat.get('user2', {})
    
    if current_user.id not in [user1.get('id'), user2.get('id')]:
        raise HTTPException(status_code=403, detail="You are not in this chat")

    logger.info(f"User {current_user.username} left chat {chat_id}")
    chat_manager.remove_chat(chat_id)
    return {"status": "left"}

@router.get("/waiting-status")
async def get_waiting_status(current_user: models.User = Depends(get_current_user)):
    chat_manager.update_user_status(current_user.id)

    # เช็คถ้าอยู่ในคิวรอ
    waiting_status = chat_manager.get_waiting_status(current_user.id)
    if waiting_status:
        return waiting_status

    # เช็คถ้าอยู่ในแชท
    chat_status = chat_manager.get_active_chat_status(current_user.id)
    if chat_status:
        return chat_status

    return {"status": "not_waiting"}

@router.get("/online-users/{school}")
async def get_online_users(
    school: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    users = db.query(models.User).filter(models.User.school == school).all()
    online_count = sum(1 for user in users if chat_manager.is_user_online(user.id))

    return {
        "school": school,
        "online_users": online_count
    }

# Debug Routes
@router.get("/debug/waiting-users")
async def get_waiting_users_debug(current_user: models.User = Depends(get_current_user)):
    return {
        "waiting_users": [
            {
                "username": u.get('user', {}).get('username'),
                "school": u.get('school'),
                "online": chat_manager.is_user_online(u.get('user', {}).get('id'))
            }
            for u in chat_manager.waiting_users
        ],
        "active_chats": [
            {
                "chat_id": chat_id,
                "users": [
                    chat.get('user1', {}).get('username'),
                    chat.get('user2', {}).get('username')
                ],
                "school": chat.get('school')
            }
            for chat_id, chat in chat_manager.active_chats.items()
        ]
    }

@router.post("/debug/reset-chat")
async def reset_chat(current_user: models.User = Depends(get_current_user)):
    chat_manager.reset()
    return {"status": "reset_complete"}