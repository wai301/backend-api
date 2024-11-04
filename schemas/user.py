from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base Profile without password
class ProfileBase(BaseModel):
    username: str
    email: EmailStr
    school: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    interests: List[str] = []
    profile_pic: Optional[str] = None

# Profile for registration with password
class ProfileCreate(ProfileBase):
    password: str

# Complete Profile with additional fields
class Profile(ProfileBase):
    created_at: datetime
    last_online: Optional[datetime] = None
    stats: Dict[str, Any] = {
        "total_chats": 0,
        "rating_avg": 0,
        "rating_count": 0
    }

# For updating profile
class ProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    school: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None