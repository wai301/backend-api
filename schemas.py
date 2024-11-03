# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base Schemas
class FirebaseModel(BaseModel):
    """Base model with Firebase config"""
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Chat Message Schemas
class ChatMessage(FirebaseModel):
    content: str
    emoji: Optional[str] = None

class ChatRating(FirebaseModel):
    score: int  # 1-5
    comment: Optional[str] = None
    chat_id: str
    rated_user_id: str
    rated_by_user_id: str

# User Schemas
class UserBase(FirebaseModel):
    username: str
    email: EmailStr
    school: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str  # Firebase document ID
    display_name: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = []
    profile_pic: Optional[str] = None
    created_at: datetime
    last_online: Optional[datetime] = None
    is_active: bool = True

# Profile Schemas
class ProfileUpdate(FirebaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    school: Optional[str] = None

class Profile(FirebaseModel):
    username: str
    email: EmailStr
    school: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    interests: List[str] = []
    profile_pic: Optional[str] = None
    stats: Dict[str, int] = {
        "total_chats": 0,
        "rating_avg": 0,
        "rating_count": 0
    }

# Token Schemas
class Token(FirebaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(FirebaseModel):
    username: Optional[str] = None
    exp: Optional[datetime] = None

# Report Schemas
class ReportCreate(FirebaseModel):
    reason: str
    chat_id: Optional[str] = None
    reported_user_id: str

class Report(ReportCreate):
    id: str  # Firebase document ID
    reporter_id: str
    created_at: datetime
    status: str = "pending"  # pending, reviewed, closed
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    action_taken: Optional[str] = None

# Chat Response Schemas
class ChatPartner(FirebaseModel):
    username: str
    school: str
    online: bool
    display_name: Optional[str] = None
    profile_pic: Optional[str] = None

class ChatResponse(FirebaseModel):
    status: str  # matched, waiting
    chat_id: Optional[str] = None
    partner: Optional[ChatPartner] = None

class MessageResponse(FirebaseModel):
    id: str  # Firebase document ID
    content: str
    sender_id: str
    chat_id: str
    created_at: datetime
    is_read: bool = False
    emoji: Optional[str] = None

class ChatMessages(FirebaseModel):
    messages: List[MessageResponse]
    partner: ChatPartner
    chat_info: Dict[str, Any] = {
        "started_at": None,
        "school": None,
        "status": None
    }

# Stats Schemas
class UserStats(FirebaseModel):
    total_chats: int = 0
    total_messages: int = 0
    avg_chat_duration: float = 0
    rating_avg: float = 0
    rating_count: int = 0
    reports_received: int = 0
    reports_made: int = 0
    chat_partners: List[str] = []
    active_time: int = 0  # in minutes
    last_active: Optional[datetime] = None

# Additional Response Schemas
class OnlineUsersResponse(FirebaseModel):
    school: str
    online_users: int
    total_users: int

class ChatStatus(FirebaseModel):
    status: str  # active, waiting, ended
    partner: Optional[ChatPartner] = None
    last_message: Optional[MessageResponse] = None
    started_at: Optional[datetime] = None
    school: Optional[str] = None