from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Chat Message Schemas
class ChatMessage(BaseModel):
    content: str
    emoji: Optional[str] = None

class ChatRating(BaseModel):
    score: int  # 1-5
    comment: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    username: str
    email: str
    school: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True  # เดิมใช้ orm_mode = True ในเวอร์ชั่นใหม่ใช้ from_attributes

# Profile Schemas
class Profile(BaseModel):
    id: int
    username: str
    email: str
    school: str
    
    class Config:
        from_attributes = True

class ProfileUpdate(BaseModel):
    email: Optional[str] = None
    school: Optional[str] = None
    
    class Config:
        from_attributes = True

class Profile(BaseModel):
    id: int
    username: str
    email: str
    school: str
    
    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Report Schemas
class ReportBase(BaseModel):
    reason: str

class Report(ReportBase):
    id: int
    reporter_id: int
    reported_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Chat Response Schemas
class ChatPartner(BaseModel):
    username: str
    school: str
    online: bool

class ChatResponse(BaseModel):
    status: str
    chat_id: Optional[str] = None
    partner: Optional[ChatPartner] = None

class MessageResponse(BaseModel):
    content: str
    sender_id: int
    sender_username: str
    timestamp: str

class ChatMessages(BaseModel):
    messages: List[MessageResponse]
    partner: ChatPartner