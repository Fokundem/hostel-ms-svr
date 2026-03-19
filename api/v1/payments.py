from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from services.payment import PaymentService
from schemas.payment import PaymentResponse, PaymentCreate, PaymentSummary, PaymentAdminReview
from utils.dependencies import get_current_user, get_current_admin, get_current_student
from models import Student, Payment
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import secrets
from services.notification import NotificationService

router = APIRouter(prefix="/payments", tags=["Payments"])


def _get_student_by_user_id(db: Session, user_id: str):
    return db.execute(select(Student).where(Student.userId == user_id)).scalar_one_or_none()


@router.get("/student/my-payments", response_model=List[PaymentResponse])
def get_my_payments(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_student)
):
    """Get current student's payments"""
    try:
        student = _get_student_by_user_id(db, current_user.id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
        service = PaymentService(db)
        payments = service.get_student_payments(student.id)
        return payments
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/student/summary", response_model=PaymentSummary)
def get_payment_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_student)
):
    """Get payment summary for current student"""
    try:
        student = _get_student_by_user_id(db, current_user.id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
        service = PaymentService(db)
        summary = service.get_payment_summary(student.id)
        return summary
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=List[dict])
def get_all_payments(
    filter_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get all payments (admin only)"""
    try:
        service = PaymentService(db)
        payments = service.get_all_payments(status=filter_status)
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
    db: Session = Depends(get_db),
    current_user=Depends(get_current_student),
):
    """Student submits a payment with proof screenshot (multipart/form-data)."""
    student = _get_student_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

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
    payment = service.submit_payment_proof(
        student_id=student.id,
        amount=amount,
        payment_type=type,
        month=month,
        year=year,
        method=method,
        proof_image_url=proof_url,
    )
    NotificationService(db).create_for_roles(
        roles=["ADMIN", "HOSTEL_MANAGER"],
        title="Payment proof submitted",
        message=f"{current_user.name} submitted a payment proof for review.",
        type_value="SYSTEM",
        data={"link": "/admin/payments", "paymentId": payment["id"]},
    )
    return {"message": "Payment submitted for review", "payment": payment}


@router.put("/{payment_id}/review", response_model=dict)
def admin_review_payment(
    payment_id: str,
    payload: PaymentAdminReview,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Admin approves/rejects a submitted payment."""
    payment = db.execute(select(Payment).where(Payment.id == payment_id)).scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    service = PaymentService(db)
    updated = service.admin_review_payment(
        payment_id=payment_id,
        status_value=payload.status,
        reviewed_by=current_user.id,
        rejection_reason=payload.rejectionReason,
    )
    student = db.execute(select(Student).where(Student.id == updated["studentId"])).scalar_one_or_none()
    if student:
        NotificationService(db).create_for_user(
            user_id=student.userId,
            title="Payment reviewed",
            message=f"Your payment was {updated['status'].lower()}.",
            type_value="SYSTEM",
            data={"link": "/student/payments", "paymentId": updated["id"]},
        )
    return {"message": "Payment reviewed", "payment": updated}


@router.post("/{student_id}", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_payment(
    student_id: str,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create a payment record (admin only)"""
    try:
        student = db.execute(select(Student).where(Student.id == student_id)).scalar_one_or_none()
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        service = PaymentService(db)
        payment = service.create_payment(student_id, payment_data)
        return {"message": "Payment record created successfully", "payment": payment}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{payment_id}/mark-paid", response_model=dict)
def mark_payment_paid(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Mark a payment as paid"""
    try:
        payment = db.execute(select(Payment).where(Payment.id == payment_id)).scalar_one_or_none()
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        student = _get_student_by_user_id(db, current_user.id)
        role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if student and student.id != payment.studentId and role_val not in ["ADMIN", "HOSTEL_MANAGER"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        service = PaymentService(db)
        updated_payment = service.mark_payment_paid(payment_id)
        return {"message": "Payment marked as paid", "payment": updated_payment}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
