from prisma import Prisma
from schemas.payment import PaymentCreate, PaymentUpdate
from typing import Optional, List
from datetime import datetime


class PaymentService:
    def __init__(self, db: Prisma):
        self.db = db

    async def get_student_payments(self, student_id: str) -> List[dict]:
        """Get all payments for a student"""
        payments = await self.db.payment.find_many(
            where={"studentId": student_id},
            order={"createdAt": "desc"}
        )
        
        return [
            {
                "id": payment.id,
                "studentId": payment.studentId,
                "amount": payment.amount,
                "type": payment.type,
                "month": payment.month,
                "year": payment.year,
                "status": payment.status,
                "method": getattr(payment, "method", None),
                "proofImageUrl": getattr(payment, "proofImageUrl", None),
                "rejectionReason": getattr(payment, "rejectionReason", None),
                "reviewedAt": payment.reviewedAt.isoformat() if getattr(payment, "reviewedAt", None) else None,
                "reviewedBy": getattr(payment, "reviewedBy", None),
                "paidAt": payment.paidAt.isoformat() if payment.paidAt else None,
                "createdAt": payment.createdAt.isoformat(),
            }
            for payment in payments
        ]

    async def get_payment_summary(self, student_id: str) -> dict:
        """Get payment summary for a student"""
        payments = await self.db.payment.find_many(
            where={"studentId": student_id}
        )
        
        total_due = sum(p.amount for p in payments if p.status in ["PENDING", "OVERDUE", "REJECTED"])
        total_paid = sum(p.amount for p in payments if p.status in ["APPROVED", "PAID"])
        total_overdue = sum(p.amount for p in payments if p.status == "OVERDUE")
        
        return {
            "totalDue": total_due,
            "totalPaid": total_paid,
            "totalOverdue": total_overdue,
            "pendingCount": len([p for p in payments if p.status == "PENDING"]),
            "paidCount": len([p for p in payments if p.status in ["APPROVED", "PAID"]]),
            "overdueCount": len([p for p in payments if p.status == "OVERDUE"]),
        }

    async def create_payment(self, student_id: str, payment_data: PaymentCreate) -> dict:
        """Create a payment record (admin only)"""
        payment = await self.db.payment.create(
            data={
                "studentId": student_id,
                "amount": payment_data.amount,
                "type": payment_data.type,
                "month": payment_data.month,
                "year": payment_data.year,
                "status": "PENDING",
                "method": getattr(payment_data, "method", "BANK_TRANSFER"),
            }
        )
        
        return {
            "id": payment.id,
            "studentId": payment.studentId,
            "amount": payment.amount,
            "type": payment.type,
            "month": payment.month,
            "year": payment.year,
            "status": payment.status,
            "method": payment.method,
            "proofImageUrl": payment.proofImageUrl,
            "createdAt": payment.createdAt.isoformat(),
        }

    async def submit_payment_proof(
        self,
        student_id: str,
        amount: float,
        payment_type: str,
        month: int,
        year: int,
        method: str,
        proof_image_url: str,
    ) -> dict:
        payment = await self.db.payment.create(
            data={
                "studentId": student_id,
                "amount": amount,
                "type": payment_type,
                "month": month,
                "year": year,
                "status": "SUBMITTED",
                "method": method,
                "proofImageUrl": proof_image_url,
            }
        )
        return {
            "id": payment.id,
            "studentId": payment.studentId,
            "amount": payment.amount,
            "type": payment.type,
            "month": payment.month,
            "year": payment.year,
            "status": payment.status,
            "method": payment.method,
            "proofImageUrl": payment.proofImageUrl,
            "createdAt": payment.createdAt.isoformat(),
        }

    async def admin_review_payment(
        self,
        payment_id: str,
        status_value: str,
        reviewed_by: str,
        rejection_reason: Optional[str] = None,
    ) -> dict:
        data = {
            "status": status_value,
            "reviewedAt": datetime.utcnow(),
            "reviewedBy": reviewed_by,
        }
        if status_value in ["APPROVED", "PAID"]:
            data["paidAt"] = datetime.utcnow()
            data["rejectionReason"] = None
        if status_value == "REJECTED":
            data["rejectionReason"] = rejection_reason or "Rejected"

        payment = await self.db.payment.update(where={"id": payment_id}, data=data)
        return {
            "id": payment.id,
            "studentId": payment.studentId,
            "amount": payment.amount,
            "type": payment.type,
            "month": payment.month,
            "year": payment.year,
            "status": payment.status,
            "method": payment.method,
            "proofImageUrl": payment.proofImageUrl,
            "rejectionReason": payment.rejectionReason,
            "reviewedAt": payment.reviewedAt.isoformat() if payment.reviewedAt else None,
            "reviewedBy": payment.reviewedBy,
            "paidAt": payment.paidAt.isoformat() if payment.paidAt else None,
            "createdAt": payment.createdAt.isoformat(),
        }

    async def mark_payment_paid(self, payment_id: str) -> dict:
        """Mark a payment as paid"""
        payment = await self.db.payment.update(
            where={"id": payment_id},
            data={
                "status": "PAID",
                "paidAt": datetime.utcnow(),
                "reviewedAt": datetime.utcnow(),
            }
        )
        
        return {
            "id": payment.id,
            "studentId": payment.studentId,
            "amount": payment.amount,
            "type": payment.type,
            "month": payment.month,
            "year": payment.year,
            "status": payment.status,
            "method": getattr(payment, "method", None),
            "proofImageUrl": getattr(payment, "proofImageUrl", None),
            "paidAt": payment.paidAt.isoformat() if payment.paidAt else None,
            "createdAt": payment.createdAt.isoformat(),
        }

    async def get_all_payments(self, status: Optional[str] = None) -> List[dict]:
        """Get all payments (admin view)"""
        filters = {}
        if status:
            filters["status"] = status
        
        payments = await self.db.payment.find_many(
            where=filters,
            include={"student": True},
            order={"createdAt": "desc"}
        )
        
        return [
            {
                "id": payment.id,
                "studentId": payment.studentId,
                "studentName": payment.student.user.name,
                "amount": payment.amount,
                "type": payment.type,
                "month": payment.month,
                "year": payment.year,
                "status": payment.status,
                "method": getattr(payment, "method", None),
                "proofImageUrl": getattr(payment, "proofImageUrl", None),
                "rejectionReason": getattr(payment, "rejectionReason", None),
                "reviewedAt": payment.reviewedAt.isoformat() if getattr(payment, "reviewedAt", None) else None,
                "reviewedBy": getattr(payment, "reviewedBy", None),
                "paidAt": payment.paidAt.isoformat() if payment.paidAt else None,
                "createdAt": payment.createdAt.isoformat(),
            }
            for payment in payments
        ]
