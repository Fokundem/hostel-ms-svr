from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database import get_db
from app.services.payment import PaymentService
from app.schemas.payment import PaymentResponse, PaymentCreate, PaymentSummary
from app.utils.dependencies import get_current_user, get_current_admin, get_current_student
from prisma import Prisma
from typing import Optional, List

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/student/my-payments", response_model=List[PaymentResponse])
async def get_my_payments(
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_student)
):
    """Get current student's payments"""
    try:
        # Get student profile
        student = await db.student.find_unique(where={"userId": current_user.id})
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
        
        service = PaymentService(db)
        payments = await service.get_student_payments(student.id)
        return payments
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/student/summary", response_model=PaymentSummary)
async def get_payment_summary(
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_student)
):
    """Get payment summary for current student"""
    try:
        # Get student profile
        student = await db.student.find_unique(where={"userId": current_user.id})
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
        
        service = PaymentService(db)
        summary = await service.get_payment_summary(student.id)
        return summary
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=List[dict])
async def get_all_payments(
    status: Optional[str] = Query(None),
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get all payments (admin only)"""
    try:
        service = PaymentService(db)
        payments = await service.get_all_payments(status=status)
        return payments
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{student_id}", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_payment(
    student_id: str,
    payment_data: PaymentCreate,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create a payment record (admin only)"""
    try:
        # Verify student exists
        student = await db.student.find_unique(where={"id": student_id})
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        
        service = PaymentService(db)
        payment = await service.create_payment(student_id, payment_data)
        
        return {
            "message": "Payment record created successfully",
            "payment": payment
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{payment_id}/mark-paid", response_model=dict)
async def mark_payment_paid(
    payment_id: str,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Mark a payment as paid"""
    try:
        payment = await db.payment.find_unique(where={"id": payment_id})
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        
        # Check if user is student making payment or admin
        student = await db.student.find_unique(where={"userId": current_user.id})
        if student and student.id != payment.studentId and current_user.role not in ["ADMIN", "HOSTEL_MANAGER"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        service = PaymentService(db)
        updated_payment = await service.mark_payment_paid(payment_id)
        
        return {
            "message": "Payment marked as paid",
            "payment": updated_payment
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
