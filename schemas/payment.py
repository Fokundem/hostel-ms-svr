from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============ Payment Schemas ============

class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    type: str = Field(default="HOSTEL_FEE", description="HOSTEL_FEE, MAINTENANCE, OTHER")
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000)
    method: str = Field(
        default="BANK_TRANSFER",
        description="BANK_TRANSFER, POS, CASH, MOBILE_MONEY, OTHER",
    )


class PaymentAdminReview(BaseModel):
    status: str = Field(..., description="APPROVED, REJECTED, PAID")
    rejectionReason: Optional[str] = None


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
    method: Optional[str] = None
    proofImageUrl: Optional[str] = None
    rejectionReason: Optional[str] = None
    reviewedAt: Optional[datetime] = None
    reviewedBy: Optional[str] = None
    paidAt: Optional[datetime]
    createdAt: datetime

    class Config:
        from_attributes = True


class StudentPaymentResponse(PaymentResponse):
    """Response for student viewing their payments"""
    pass


class PaymentSummary(BaseModel):
    totalDue: float
    totalPaid: float
    totalOverdue: float
    pendingCount: int
    paidCount: int
    overdueCount: int
