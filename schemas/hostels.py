from pydantic import BaseModel, Field
from datetime import datetime


class HostelCreate(BaseModel):
    name: str = Field(..., min_length=2)
    code: str = Field(..., min_length=2)
    totalRooms: int = Field(..., ge=0)


class HostelResponse(BaseModel):
    id: str
    name: str
    code: str
    totalRooms: int
    createdAt: datetime
    updatedAt: datetime

