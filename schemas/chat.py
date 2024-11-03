from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    content: str
    emoji: Optional[str] = None

class ChatPartner(BaseModel):
    username: str
    school: str
    online: bool
    display_name: Optional[str] = None

class ChatResponse(BaseModel):
    status: str  # matched, waiting
    chat_id: Optional[str] = None
    partner: Optional[ChatPartner] = None

class MessageResponse(BaseModel):
    id: str
    content: str
    sender_id: str
    timestamp: datetime