from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class StudentResponse(BaseModel):
    id: str
    userId: str
    name: str
    email: EmailStr
    matricule: str
    department: str
    level: str
    phone: Optional[str] = None
    guardianContact: Optional[str] = None
    roomId: Optional[str] = None
    assignedRoom: Optional[str] = None
    role: str
    status: str
    createdAt: datetime


class StudentCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2)
    phone: Optional[str] = None
    matricule: str
    department: str
    level: str
    guardianContact: Optional[str] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    guardianContact: Optional[str] = None
    department: Optional[str] = None
    level: Optional[str] = None
    role: Optional[str] = Field(default=None, description="ADMIN, HOSTEL_MANAGER, STUDENT, EMPLOYEE")
    status: Optional[str] = Field(default=None, description="ACTIVE, INACTIVE, SUSPENDED")
    roomId: Optional[str] = None

