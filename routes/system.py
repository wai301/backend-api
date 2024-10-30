from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from utils.auth import get_current_user
from utils.chat import chat_manager
import models
from logging_config import logger

router = APIRouter()

@router.get("/status")
async def get_system_status(current_user: models.User = Depends(get_current_user)):
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
async def get_system_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        total_users = db.query(models.User).count()
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