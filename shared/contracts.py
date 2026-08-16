from datetime import datetime
from typing import Optional
from pydantic import BaseModel,Field

"""Tüm tip kontratları"""

# Auth Service -> Redis (Session) -> User Response Service
class UserSessionPayload(BaseModel):
    user_id: int
    hotel_id: str
    email: str
    role: str = "hotel_admin"
    created_at: datetime = Field(default_factory=datetime.utcnow) 