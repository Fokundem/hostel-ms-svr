from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# ============ Auth Schemas ============

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    name: str = Field(..., min_length=2, description="Name must be at least 2 characters")
    phone: Optional[str] = None
    role: str = Field(default="STUDENT", description="STUDENT, ADMIN, HOSTEL_MANAGER, EMPLOYEE")

    # Student-specific fields
    matricule: Optional[str] = None
    department: Optional[str] = None
    level: Optional[str] = None
    guardianContact: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


# ============ User Schemas ============

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    phone: Optional[str]
    avatar: Optional[str]
    status: str
    createdAt: str

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None


class StudentDetail(UserResponse):
    matricule: Optional[str]
    department: Optional[str]
    level: Optional[str]
    guardianContact: Optional[str]
    roomId: Optional[str]

    class Config:
        from_attributes = True
