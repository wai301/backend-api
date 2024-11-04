from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from models import User as UserModel
from schemas import ChatMessage, ChatResponse, MessageResponse
from utils.auth import get_current_user
from utils.chat import chat_manager
from logging_config import logger

router = APIRouter()

@router.post("/send", response_model=MessageResponse)
async def send_message(
    message: ChatMessage,
    current_user: Annotated[str, Depends(get_current_user)]
):
    try:
        result = await chat_manager.send_message(current_user, message.content)
        logger.info(f"Message sent by {current_user}")
        return result
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/match", response_model=ChatResponse)
async def match_chat(current_user: Annotated[str, Depends(get_current_user)]):
    try:
        match_result = await chat_manager.find_match(current_user)
        logger.info(f"Match result for {current_user}: {match_result}")
        return match_result
    except Exception as e:
        logger.error(f"Error in match_chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/end")
async def end_chat(current_user: Annotated[str, Depends(get_current_user)]):
    try:
        await chat_manager.end_chat(current_user)
        logger.info(f"Chat ended by {current_user}")
        return {"message": "Chat ended successfully"}
    except Exception as e:
        logger.error(f"Error in end_chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))