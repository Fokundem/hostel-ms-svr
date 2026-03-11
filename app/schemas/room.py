from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============ Room Schemas ============

class RoomCreate(BaseModel):
    roomNumber: str
    floor: str
    block: str
    hostelId: str
    capacity: int
    amenities: List[str] = []
    price: float


class RoomUpdate(BaseModel):
    roomNumber: Optional[str] = None
    floor: Optional[str] = None
    block: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None
    amenities: Optional[List[str]] = None
    price: Optional[float] = None


class RoomResponse(BaseModel):
    id: str
    roomNumber: str
    floor: str
    block: str
    capacity: int
    occupied: int
    status: str
    amenities: List[str]
    price: float
    createdAt: datetime

    class Config:
        from_attributes = True


class RoomDetailResponse(RoomResponse):
    hostelId: str
    
    class Config:
        from_attributes = True


# ============ Allocation Schemas ============

class RoomAllocationCreate(BaseModel):
    roomId: str


class RoomAllocationUpdateStatus(BaseModel):
    status: str  # APPROVED or REJECTED
    rejectionReason: Optional[str] = None


class RoomAllocationResponse(BaseModel):
    id: str
    studentId: str
    roomId: str
    status: str
    requestedAt: datetime
    approvedAt: Optional[datetime] = None
    approvedBy: Optional[str] = None
    rejectionReason: Optional[str] = None

    class Config:
        from_attributes = True


class RoomAllocationDetailResponse(RoomAllocationResponse):
    student: dict
    room: RoomResponse

    class Config:
        from_attributes = True


class StudentAllocationResponse(BaseModel):
    """Response for student to see their allocation"""
    id: str
    roomId: str
    status: str
    requestedAt: datetime
    approvedAt: Optional[datetime] = None
    room: RoomResponse

    class Config:
        from_attributes = True
