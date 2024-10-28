from pydantic import BaseModel
from typing import Optional, List

class ChatMessage(BaseModel):
    content: str
    emoji: Optional[str] = None

class ChatRating(BaseModel):
    score: int  # 1-5
    comment: Optional[str] = None