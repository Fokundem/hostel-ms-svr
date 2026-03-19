from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ComplaintCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=5)
    category: str = Field(default="OTHER", description="MAINTENANCE, SECURITY, CLEANLINESS, NOISE, OTHER")
    priority: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH")


class ComplaintAdminUpdate(BaseModel):
    status: Optional[str] = Field(default=None, description="PENDING, IN_PROGRESS, RESOLVED")
    adminResponse: Optional[str] = None
    priority: Optional[str] = Field(default=None, description="LOW, MEDIUM, HIGH")


class ComplaintResponse(BaseModel):
    id: str
    studentId: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    adminResponse: Optional[str] = None
    resolvedAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime


class ComplaintAdminListItem(ComplaintResponse):
    studentName: str
    roomNumber: Optional[str] = None

