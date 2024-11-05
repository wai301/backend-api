from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from datetime import datetime
from utils.auth import get_current_user
from utils.chat import chat_manager
from logging_config import logger
from firebase_config import db

router = APIRouter()

@router.post("/update-status")
async def update_status(current_user: Annotated[str, Depends(get_current_user)]):
    try:
        # เช็คสถานะของผู้ใช้
        user_status = await chat_manager.get_user_status(current_user)
        logger.info(f"Status update for {current_user}: {user_status}")
        return {
            "status": "online" if user_status else "offline",
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in update_status: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
async def get_system_status(current_user: Annotated[str, Depends(get_current_user)]):
    try:
        return {
            "status": "healthy",
            "waiting_users_count": len(chat_manager.waiting_users),
            "active_chats_count": len(chat_manager.active_chats),
            "online_users_count": len(chat_manager.online_users),
            "current_time": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {
            "status": "error",
            "detail": str(e)
        }

@router.get("/stats")
async def get_system_stats(current_user: Annotated[str, Depends(get_current_user)]):
    try:
        # ดึงข้อมูลจาก Firebase
        users_ref = db.collection('users')
        total_users = len(list(users_ref.stream()))
        active_users = len(chat_manager.online_users)
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "active_chats": len(chat_manager.active_chats),
            "waiting_users": len(chat_manager.waiting_users)
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return {
            "status": "error",
            "detail": str(e)
        }

@router.get("/health")
async def health_check():
    """Basic health check endpoint that doesn't require authentication"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }