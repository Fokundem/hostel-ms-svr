from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class NotificationResponse(BaseModel):
    id: str
    userId: str
    title: str
    message: str
    type: str
    read: bool
    data: Optional[Any] = None
    createdAt: datetime


class NotificationCreate(BaseModel):
    userId: str
    title: str
    message: str
    type: str = "SYSTEM"
    data: Optional[Any] = None

