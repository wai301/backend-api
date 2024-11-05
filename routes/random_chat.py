from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from datetime import datetime
from models import User as UserModel
from schemas import ChatMessage, ChatResponse
from utils.auth import get_current_user
from utils.chat import chat_manager
from logging_config import logger

router = APIRouter()

@router.post("/start-chat")
async def start_random_chat(current_user: Annotated[str, Depends(get_current_user)]):
    try:
        # เริ่มการแชทแบบสุ่ม
        result = await chat_manager.start_random_chat(current_user)
        logger.info(f"Random chat started for user: {current_user}")
        return result
    except Exception as e:
        logger.error(f"Error starting random chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/end-chat")
async def end_random_chat(current_user: Annotated[str, Depends(get_current_user)]):
    try:
        # จบการแชท
        await chat_manager.end_chat(current_user)
        logger.info(f"Chat ended by {current_user}")
        return {"message": "Chat ended successfully"}
    except Exception as e:
        logger.error(f"Error ending chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
async def get_chat_status(current_user: Annotated[str, Depends(get_current_user)]):
    try:
        # เช็คสถานะการแชท
        status = await chat_manager.get_chat_status(current_user)
        return status
    except Exception as e:
        logger.error(f"Error getting chat status: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/send")
async def send_message(
    message: ChatMessage,
    current_user: Annotated[str, Depends(get_current_user)]
):
    try:
        result = await chat_manager.send_message(current_user, message.content)
        logger.info(f"Message sent by {current_user}")
        return result
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))