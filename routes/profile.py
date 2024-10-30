from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from utils.auth import get_current_user
from database import get_db
import models, schemas
from logging_config import logger

router = APIRouter()

@router.get("/profile", response_model=schemas.Profile)
async def get_profile(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.post("/profile/update")
async def update_profile(
    profile_update: schemas.ProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if profile_update.email:
            existing_user = db.query(models.User).filter(
                models.User.email == profile_update.email,
                models.User.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="อีเมลนี้ถูกใช้งานแล้ว")
            current_user.email = profile_update.email
            
        if profile_update.school:
            current_user.school = profile_update.school
            
        db.commit()
        db.refresh(current_user)
        
        return {
            "status": "success",
            "message": "อัพเดทข้อมูลสำเร็จ",
            "user": current_user
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))