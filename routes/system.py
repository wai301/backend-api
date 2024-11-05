from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from datetime import datetime
from utils.auth import get_current_user
from utils.chat import chat_manager
from logging_config import logger
from firebase_config import db

router = APIRouter()

@router.post("/update-status")
@router.options("/update-status")  # เพิ่ม options method
async def update_status():  # ลบ current_user dependency
    try:
        return {
            "status": "online",
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

@router.get("/health")
async def health_check():
    """Basic health check endpoint that doesn't require authentication"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }