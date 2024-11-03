from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Annotated
from schemas import UserCreate, User, Token
from utils.auth import (
    create_access_token, 
    get_password_hash, 
    verify_password, 
    get_current_user
)
from models import User as UserModel
from utils.chat import chat_manager
from config import settings
from logging_config import logger

router = APIRouter()

@router.post("/register", response_model=User)
async def register(user: UserCreate):
    logger.info(f"Received registration request: {user.username}")
    
    try:
        # เช็คว่ามี username ซ้ำไหม
        existing_user = await UserModel.get_by_username(user.username)
        if existing_user:
            logger.error(f"Username already registered: {user.username}")
            raise HTTPException(
                status_code=400, 
                detail="Username already registered"
            )

        # เช็คว่ามี email ซ้ำไหม
        existing_email = await UserModel.get_by_email(user.email)
        if existing_email:
            logger.error(f"Email already registered: {user.email}")
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        # Hash password
        hashed_password = get_password_hash(user.password)
        
        # สร้างข้อมูลผู้ใช้
        user_data = {
            "username": user.username,
            "email": user.email,
            "hashed_password": hashed_password,
            "school": user.school
        }

        # สร้างผู้ใช้ใน Firebase
        user_id = await UserModel.create(user_data)
        logger.info(f"User registered successfully: {user.username}")

        # ดึงข้อมูลผู้ใช้ที่สร้างเสร็จ
        new_user = await UserModel.get_by_username(user_id)
        
        # อัพเดทสถานะออนไลน์
        await chat_manager.update_user_status(user_id)
        
        return new_user

    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # ดึงข้อมูลผู้ใช้จาก username
        user = await UserModel.get_by_username(form_data.username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        # เช็ครหัสผ่าน
        if not verify_password(form_data.password, user['hashed_password']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        # อัพเดทสถานะออนไลน์
        await chat_manager.update_user_status(user['username'])
        logger.info(f"User logged in: {user['username']}")

        # สร้าง token
        access_token = create_access_token(
            data={"sub": user['username']},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login failed"
        )

@router.post("/logout")
async def logout(current_user: Annotated[str, Depends(get_current_user)]):
    try:
        # อัพเดทสถานะออฟไลน์
        await chat_manager.remove_user_status(current_user)
        logger.info(f"User logged out: {current_user}")
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))