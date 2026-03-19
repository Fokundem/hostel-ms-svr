from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VisitorRequestCreate(BaseModel):
    name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=6)
    purpose: str = Field(..., min_length=2)


class VisitorAdminDecision(BaseModel):
    status: str = Field(..., description="APPROVED or REJECTED")
    rejectionReason: Optional[str] = None


class VisitorResponse(BaseModel):
    id: str
    name: str
    phone: str
    purpose: str
    studentId: str
    studentName: str
    roomNumber: str
    status: str
    requestedAt: Optional[datetime] = None
    approvedAt: Optional[datetime] = None
    approvedBy: Optional[str] = None
    rejectionReason: Optional[str] = None
    entryTime: Optional[datetime] = None
    exitTime: Optional[datetime] = None
    createdAt: datetime

