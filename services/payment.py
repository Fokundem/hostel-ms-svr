from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc
from datetime import datetime
from typing import Optional, List

from models import Payment, Student, PaymentStatusEnum, PaymentTypeEnum
from schemas.payment import PaymentCreate


def _payment_to_dict(payment: Payment, include_student_name: bool = False) -> dict:
    status_val = payment.status.value if hasattr(payment.status, "value") else str(payment.status)
    type_val = payment.type.value if hasattr(payment.type, "value") else str(payment.type)
    out = {
        "id": payment.id,
        "studentId": payment.studentId,
        "amount": payment.amount,
        "type": type_val,
        "month": payment.month,
        "year": payment.year,
        "status": status_val,
        "method": getattr(payment, "method", None),
        "proofImageUrl": getattr(payment, "proofImageUrl", None),
        "rejectionReason": getattr(payment, "rejectionReason", None),
        "reviewedAt": payment.reviewedAt.isoformat() if payment.reviewedAt else None,
        "reviewedBy": getattr(payment, "reviewedBy", None),
        "reviewedByName": getattr(payment, "_reviewedByName", None),
        "paidAt": payment.paidAt.isoformat() if payment.paidAt else None,
        "createdAt": payment.createdAt.isoformat() if payment.createdAt else None,
    }
    if include_student_name and payment.student and payment.student.user:
        out["studentName"] = payment.student.user.name
    return out


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    def get_student_payments(self, student_id: str) -> List[dict]:
        payments = self.db.execute(
            select(Payment).where(Payment.studentId == student_id).order_by(desc(Payment.createdAt))
        ).scalars().all()
        
        admin_ids = {p.reviewedBy for p in payments if p.reviewedBy}
        admin_names = {}
        if admin_ids:
            from models import User
            admins = self.db.execute(select(User.id, User.name).where(User.id.in_(admin_ids))).all()
            admin_names = {a.id: a.name for a in admins}
            
        for p in payments:
            setattr(p, "_reviewedByName", admin_names.get(p.reviewedBy) if p.reviewedBy else None)
            
        return [_payment_to_dict(p) for p in payments]

    def get_payment_summary(self, student_id: str) -> dict:
        payments = self.db.execute(select(Payment).where(Payment.studentId == student_id)).scalars().all()
        status_vals = [p.status.value if hasattr(p.status, "value") else str(p.status) for p in payments]
        total_due = sum(p.amount for p, s in zip(payments, status_vals) if s in ["PENDING", "OVERDUE", "REJECTED"])
        total_paid = sum(p.amount for p, s in zip(payments, status_vals) if s in ["APPROVED", "PAID"])
        total_overdue = sum(p.amount for p, s in zip(payments, status_vals) if s == "OVERDUE")
        return {
            "totalDue": total_due,
            "totalPaid": total_paid,
            "totalOverdue": total_overdue,
            "pendingCount": sum(1 for s in status_vals if s == "PENDING"),
            "paidCount": sum(1 for s in status_vals if s in ["APPROVED", "PAID"]),
            "overdueCount": sum(1 for s in status_vals if s == "OVERDUE"),
        }

    def create_payment(self, student_id: str, payment_data: PaymentCreate) -> dict:
        type_val = getattr(payment_data, "type", "HOSTEL_FEE")
        if isinstance(type_val, str):
            type_val = PaymentTypeEnum(type_val) if type_val in [e.value for e in PaymentTypeEnum] else PaymentTypeEnum.HOSTEL_FEE
        payment = Payment(
            studentId=student_id,
            amount=payment_data.amount,
            type=type_val,
            month=payment_data.month,
            year=payment_data.year,
            status=PaymentStatusEnum.PENDING,
            method=getattr(payment_data, "method", "BANK_TRANSFER"),
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return _payment_to_dict(payment)

    def submit_payment_proof(
        self,
        student_id: str,
        amount: float,
        payment_type: str,
        month: int,
        year: int,
        method: str,
        proof_image_url: str,
    ) -> dict:
        type_enum = PaymentTypeEnum(payment_type) if payment_type in [e.value for e in PaymentTypeEnum] else PaymentTypeEnum.HOSTEL_FEE
        payment = Payment(
            studentId=student_id,
            amount=amount,
            type=type_enum,
            month=month,
            year=year,
            status=PaymentStatusEnum.SUBMITTED,
            method=method,
            proofImageUrl=proof_image_url,
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return _payment_to_dict(payment)

    def admin_review_payment(
        self,
        payment_id: str,
        status_value: str,
        reviewed_by: str,
        rejection_reason: Optional[str] = None,
    ) -> dict:
        payment = self.db.execute(select(Payment).where(Payment.id == payment_id)).scalar_one_or_none()
        if not payment:
            raise ValueError("Payment not found")
        payment.status = PaymentStatusEnum(status_value)
        payment.reviewedAt = datetime.utcnow()
        payment.reviewedBy = reviewed_by
        if status_value in ["APPROVED", "PAID"]:
            payment.paidAt = datetime.utcnow()
            payment.rejectionReason = None
        elif status_value == "REJECTED":
            payment.rejectionReason = rejection_reason or "Rejected"
        self.db.commit()
        self.db.refresh(payment)
        return _payment_to_dict(payment)

    def mark_payment_paid(self, payment_id: str) -> dict:
        payment = self.db.execute(select(Payment).where(Payment.id == payment_id)).scalar_one_or_none()
        if not payment:
            raise ValueError("Payment not found")
        payment.status = PaymentStatusEnum.PAID
        payment.paidAt = datetime.utcnow()
        payment.reviewedAt = datetime.utcnow()
        self.db.commit()
        self.db.refresh(payment)
        return _payment_to_dict(payment)

    def get_all_payments(self, status: Optional[str] = None) -> List[dict]:
        q = select(Payment).options(joinedload(Payment.student).joinedload(Student.user)).order_by(desc(Payment.createdAt))
        if status:
            q = q.where(Payment.status == PaymentStatusEnum(status))
        payments = self.db.execute(q).unique().scalars().all()
        
        admin_ids = {p.reviewedBy for p in payments if p.reviewedBy}
        admin_names = {}
        if admin_ids:
            from models import User
            admins = self.db.execute(select(User.id, User.name).where(User.id.in_(admin_ids))).all()
            admin_names = {a.id: a.name for a in admins}
            
        for p in payments:
            setattr(p, "_reviewedByName", admin_names.get(p.reviewedBy) if p.reviewedBy else None)
            
        return [_payment_to_dict(p, include_student_name=True) for p in payments]
