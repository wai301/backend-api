from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class ChatStart(BaseModel):
    school: str

class ChatMessage(BaseModel):
    content: str
    emoji: Optional[str] = None

class ChatPartner(BaseModel):
    username: str
    school: str
    online: bool
    display_name: Optional[str] = None

class ChatResponse(BaseModel):
    status: str
    chat_id: Optional[str] = None
    partner: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    status: str
    message_id: str

class MessagesResponse(BaseModel):
    messages: List[Dict[str, Any]]
    partner: Dict[str, Any]

class OnlineUsersResponse(BaseModel):
    school: str
    online_users: int

class WaitingUsersResponse(BaseModel):
    waiting_users: List[Dict[str, Any]]
    active_chats: List[Dict[str, Any]]

class ChatStatusResponse(BaseModel):
    status: str