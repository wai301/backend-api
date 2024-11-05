from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from datetime import datetime
from models import User as UserModel
from schemas import ChatMessage, ChatResponse
from utils.auth import get_current_user
from utils.chat import chat_manager
from logging_config import logger

router = APIRouter()

@router.options("/start-chat")
async def options_start_chat():
    return {"message": "OK"}

@router.post("/start-chat")
async def start_chat(current_user: Annotated[str, Depends(get_current_user)]):
    try:
        result = await chat_manager.start_chat(current_user)
        logger.info(f"Chat started for user: {current_user}")
        return result
    except Exception as e:
        logger.error(f"Error starting chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/waiting-status")
async def check_waiting_status(current_user: Annotated[str, Depends(get_current_user)]):
    try:
        status = await chat_manager.get_waiting_status(current_user)
        return status
    except Exception as e:
        logger.error(f"Error checking waiting status: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/chat-messages/{chat_id}")
async def get_chat_messages(
    chat_id: str,
    current_user: Annotated[str, Depends(get_current_user)]
):
    try:
        messages = await chat_manager.get_messages(chat_id, current_user)
        return messages
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/send-message/{chat_id}")
async def send_chat_message(
    chat_id: str,
    message: ChatMessage,
    current_user: Annotated[str, Depends(get_current_user)]
):
    try:
        result = await chat_manager.send_message(chat_id, current_user, message.content)
        return result
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/leave-chat/{chat_id}")
async def leave_chat(
    chat_id: str,
    current_user: Annotated[str, Depends(get_current_user)]
):
    try:
        await chat_manager.leave_chat(chat_id, current_user)
        return {"message": "Successfully left chat"}
    except Exception as e:
        logger.error(f"Error leaving chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/online-users/{school}")
async def get_online_users(
    school: str,
    current_user: Annotated[str, Depends(get_current_user)]
):
    try:
        count = await chat_manager.get_online_users_count(school)
        return {"online_users": count}
    except Exception as e:
        logger.error(f"Error getting online users: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/submit-rating")
async def submit_chat_rating(
    rating_data: dict,
    current_user: Annotated[str, Depends(get_current_user)]
):
    try:
        await chat_manager.submit_rating(
            current_user,
            rating_data["chat_id"],
            rating_data["rating"],
            rating_data.get("comment", "")
        )
        return {"message": "Rating submitted successfully"}
    except Exception as e:
        logger.error(f"Error submitting rating: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))