from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from database import get_db
from services.payment import PaymentService
from schemas.payment import PaymentResponse, PaymentCreate, PaymentSummary, PaymentAdminReview
from utils.dependencies import get_current_user, get_current_admin, get_current_student
from prisma import Prisma
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import secrets
from services.notification import NotificationService

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

@router.post("/student/submit", response_model=dict, status_code=status.HTTP_201_CREATED)
async def student_submit_payment(
    amount: float = Form(...),
    type: str = Form("HOSTEL_FEE"),
    month: int = Form(...),
    year: int = Form(...),
    method: str = Form("BANK_TRANSFER"),
    proof: UploadFile = File(...),
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_student),
):
    """Student submits a payment with proof screenshot (multipart/form-data)."""
    student = await db.student.find_unique(where={"userId": current_user.id})
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    # Save upload
    uploads_dir = Path(__file__).resolve().parents[2] / "uploads" / "payment-proofs"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    ext = (Path(proof.filename).suffix or "").lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf"]:
        raise HTTPException(status_code=400, detail="Unsupported proof file type")
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(8)}{ext}"
    file_path = uploads_dir / filename
    contents = await proof.read()
    file_path.write_bytes(contents)
    proof_url = f"/uploads/payment-proofs/{filename}"

    service = PaymentService(db)
    payment = await service.submit_payment_proof(
        student_id=student.id,
        amount=amount,
        payment_type=type,
        month=month,
        year=year,
        method=method,
        proof_image_url=proof_url,
    )
    await NotificationService(db).create_for_roles(
        roles=["ADMIN", "HOSTEL_MANAGER"],
        title="Payment proof submitted",
        message=f"{current_user.name} submitted a payment proof for review.",
        type_value="SYSTEM",
        data={"link": "/admin/payments", "paymentId": payment["id"]},
    )
    return {"message": "Payment submitted for review", "payment": payment}


@router.put("/{payment_id}/review", response_model=dict)
async def admin_review_payment(
    payment_id: str,
    payload: PaymentAdminReview,
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Admin approves/rejects a submitted payment."""
    payment = await db.payment.find_unique(where={"id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    service = PaymentService(db)
    updated = await service.admin_review_payment(
        payment_id=payment_id,
        status_value=payload.status,
        reviewed_by=current_user.id,
        rejection_reason=payload.rejectionReason,
    )
    student = await db.student.find_unique(where={"id": updated["studentId"]}, include={"user": True})
    if student and student.user:
        await NotificationService(db).create_for_user(
            user_id=student.user.id,
            title="Payment reviewed",
            message=f"Your payment was {updated['status'].lower()}.",
            type_value="SYSTEM",
            data={"link": "/student/payments", "paymentId": updated["id"]},
        )
    return {"message": "Payment reviewed", "payment": updated}


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
