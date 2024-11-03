from fastapi import APIRouter, HTTPException, Depends, status
from schemas import ProfileUpdate, Profile
from utils.auth import get_current_user
from models import User
from models.base import FirebaseError, NotFoundError
from typing import Dict, Any, List  # เพิ่ม List ตรงนี้
from logging_config import logger

router = APIRouter()

@router.post("/profile/interests")
async def update_interests(
    interests: List[str],  # ตอนนี้จะไม่ขึ้นเหลืองแล้ว
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user interests"""
    try:
        user = await User.get_by_username(current_user['username'])
        if not user:
            raise NotFoundError("User not found")
        return user
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/profile/update", response_model=Profile)
async def update_profile(
    profile_update: ProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user profile"""
    try:
        # เช็คอีเมลซ้ำ
        if profile_update.email:
            existing_user = await User.get_by_email(profile_update.email)
            if existing_user and existing_user['username'] != current_user['username']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="อีเมลนี้ถูกใช้งานแล้ว"
                )

        # สร้างข้อมูลที่จะอัพเดท
        update_data = profile_update.dict(exclude_unset=True)
        
        # อัพเดทข้อมูล
        await User.update(current_user['username'], update_data)
        
        # ดึงข้อมูลล่าสุด
        updated_user = await User.get_by_username(current_user['username'])
        if not updated_user:
            raise NotFoundError("User not found")
            
        return updated_user
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except FirebaseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# เพิ่ม endpoint สำหรับอัพเดทรูปโปรไฟล์
@router.post("/profile/picture")
async def update_profile_picture(
    profile_pic: str,  # Base64 encoded image
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update profile picture"""
    try:
        # อัพเดทรูปโปรไฟล์
        await User.update(
            current_user['username'],
            {"profile_pic": profile_pic}
        )
        
        return {
            "status": "success",
            "message": "อัพเดทรูปโปรไฟล์สำเร็จ"
        }
        
    except Exception as e:
        logger.error(f"Error updating profile picture: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# เพิ่ม endpoint สำหรับอัพเดทความสนใจ
@router.post("/profile/interests")
async def update_interests(
    interests: List[str],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user interests"""
    try:
        if len(interests) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="สามารถเพิ่มความสนใจได้สูงสุด 10 รายการ"
            )
            
        # อัพเดทความสนใจ
        await User.update(
            current_user['username'],
            {"interests": interests}
        )
        
        return {
            "status": "success",
            "message": "อัพเดทความสนใจสำเร็จ"
        }
        
    except Exception as e:
        logger.error(f"Error updating interests: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )