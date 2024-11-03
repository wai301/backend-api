# schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProfileBase(BaseModel):
    username: str
    email: EmailStr
    school: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    interests: List[str] = []
    profile_pic: Optional[str] = None

class Profile(ProfileBase):
    created_at: datetime
    last_online: Optional[datetime] = None
    stats: Dict[str, Any] = {
        "total_chats": 0,
        "rating_avg": 0,
        "rating_count": 0
    }

class ProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    school: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None