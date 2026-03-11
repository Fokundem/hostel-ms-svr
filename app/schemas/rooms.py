from pydantic import BaseModel, Field
from typing import List, Optional
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
    status: str = "AVAILABLE"


class RoomUpdate(BaseModel):
    roomNumber: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None
    amenities: Optional[List[str]] = None
    price: Optional[float] = None


class RoomResponse(BaseModel):
    id: str
    roomNumber: str
    floor: str
    block: str
    hostelId: str
    capacity: int
    occupied: int
    status: str
    amenities: List[str]
    price: float
    createdAt: Optional[str] = None

    class Config:
        from_attributes = True


# ============ Room Allocation Schemas ============

class AllocationCreate(BaseModel):
    roomId: str = Field(..., description="ID of the room to request")


class AllocationResponse(BaseModel):
    id: str
    studentId: str
    roomId: str
    status: str  # PENDING, APPROVED, REJECTED
    requestedAt: str
    approvedAt: Optional[str] = None
    approvedBy: Optional[str] = None
    rejectionReason: Optional[str] = None
    room: Optional[dict] = None  # Room details

    class Config:
        from_attributes = True


class AllocationApproveRequest(BaseModel):
    pass  # No body needed


class AllocationRejectRequest(BaseModel):
    reason: str = Field(..., description="Reason for rejection")


# ============ Payment Schemas ============

class PaymentCreate(BaseModel):
    studentId: str
    amount: float
    type: str = "HOSTEL_FEE"  # HOSTEL_FEE, MAINTENANCE, OTHER
    month: int
    year: int


class PaymentUpdate(BaseModel):
    status: str  # PAID, PENDING, OVERDUE


class PaymentResponse(BaseModel):
    id: str
    studentId: str
    amount: float
    type: str
    month: int
    year: int
    status: str
    paidAt: Optional[str] = None
    createdAt: str

    class Config:
        from_attributes = True


class PaymentSummaryResponse(BaseModel):
    totalPayments: float = 0
    totalPaid: float = 0
    totalPending: float = 0
    totalOverdue: float = 0
    studentPayments: List[PaymentResponse] = []


# ============ Complaint Schemas ============

class ComplaintCreate(BaseModel):
    title: str
    description: str
    category: str = "OTHER"
    priority: str = "MEDIUM"


class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    adminResponse: Optional[str] = None


class ComplaintResponse(BaseModel):
    id: str
    studentId: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    adminResponse: Optional[str] = None
    resolvedAt: Optional[str] = None
    createdAt: str

    class Config:
        from_attributes = True


# ============ Visitor Schemas ============

class VisitorCreate(BaseModel):
    name: str
    phone: str
    purpose: str
    entryTime: datetime


class VisitorUpdate(BaseModel):
    exitTime: Optional[datetime] = None
    status: Optional[str] = None


class VisitorResponse(BaseModel):
    id: str
    name: str
    phone: str
    purpose: str
    roomNumber: str
    entryTime: str
    exitTime: Optional[str] = None
    status: str
    createdAt: str

    class Config:
        from_attributes = True
