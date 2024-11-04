from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from models import User as UserModel
from schemas import (
    ChatMessage, 
    ChatResponse, 
    ChatStart,
    MessagesResponse,
    MessageResponse,
    OnlineUsersResponse,
    WaitingUsersResponse,
    ChatStatusResponse
)
from utils.auth import get_current_user
from utils.chat import chat_manager
from logging_config import logger

# สร้าง router
router = APIRouter()

@router.post("/match", response_model=ChatResponse)
async def match_chat(
    chat_start: ChatStart,
    current_user: Annotated[str, Depends(get_current_user)]
):
    try:
        # หาคู่สนทนา
        match_result = await chat_manager.find_match(current_user, chat_start.school)
        logger.info(f"Match result for {current_user}: {match_result}")
        return match_result
    except Exception as e:
        logger.error(f"Error in match_chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/send", response_model=MessageResponse)
async def send_message(
    message: ChatMessage,
    current_user: Annotated[str, Depends(get_current_user)]
):
    try:
        # ส่งข้อความ
        result = await chat_manager.send_message(current_user, message.content)
        logger.info(f"Message sent by {current_user}")
        return result
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/messages/{chat_id}", response_model=MessagesResponse)
async def get_messages(
    chat_id: str,
    current_user: Annotated[str, Depends(get_current_user)]
):
    try:
        # ดึงประวัติข้อความ
        messages = await chat_manager.get_messages(chat_id, current_user)
        return messages
    except Exception as e:
        logger.error(f"Error in get_messages: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/end", response_model=ChatStatusResponse)
async def end_chat(current_user: Annotated[str, Depends(get_current_user)]):
    try:
        # จบการสนทนา
        await chat_manager.end_chat(current_user)
        logger.info(f"Chat ended by {current_user}")
        return {"status": "ended"}
    except Exception as e:
        logger.error(f"Error in end_chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/online", response_model=OnlineUsersResponse)
async def get_online_users(school: str):
    try:
        # ดึงจำนวนผู้ใช้ออนไลน์
        online_count = await chat_manager.get_online_count(school)
        return {"school": school, "online_users": online_count}
    except Exception as e:
        logger.error(f"Error in get_online_users: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status", response_model=WaitingUsersResponse)
async def get_chat_status():
    try:
        # ดึงสถานะการแชท
        status = await chat_manager.get_status()
        return status
    except Exception as e:
        logger.error(f"Error in get_chat_status: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))