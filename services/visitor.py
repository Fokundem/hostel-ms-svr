from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from models import Visitor, Student, User, VisitorStatusEnum


class VisitorService:
    def __init__(self, db: Session):
        self.db = db

    def list_visitors(self, status: Optional[str] = None) -> List[dict]:
        q = (
            select(Visitor, User.name)
            .join(Student, Student.id == Visitor.studentId)
            .join(User, User.id == Student.userId)
        )
        if status:
            q = q.where(Visitor.status == status.upper())
        q = q.order_by(desc(Visitor.createdAt))

        rows = self.db.execute(q).all()
        return [
            {
                "id": v.id,
                "name": v.name,
                "phone": v.phone,
                "purpose": v.purpose,
                "studentId": v.studentId,
                "studentName": student_name,
                "roomNumber": v.roomNumber,
                "status": v.status.value if hasattr(v.status, "value") else str(v.status),
                "requestedAt": v.requestedAt,
                "approvedAt": v.approvedAt,
                "approvedBy": v.approvedBy,
                "rejectionReason": v.rejectionReason,
                "entryTime": v.entryTime,
                "exitTime": v.exitTime,
                "createdAt": v.createdAt,
            }
            for (v, student_name) in rows
        ]

    def list_for_student(self, student_id: str) -> List[dict]:
        visitors = self.db.execute(
            select(Visitor).where(Visitor.studentId == student_id).order_by(desc(Visitor.createdAt))
        ).scalars().all()
        return [
            {
                "id": v.id,
                "name": v.name,
                "phone": v.phone,
                "purpose": v.purpose,
                "studentId": v.studentId,
                "roomNumber": v.roomNumber,
                "status": v.status.value if hasattr(v.status, "value") else str(v.status),
                "requestedAt": v.requestedAt,
                "approvedAt": v.approvedAt,
                "approvedBy": v.approvedBy,
                "rejectionReason": v.rejectionReason,
                "entryTime": v.entryTime,
                "exitTime": v.exitTime,
                "createdAt": v.createdAt,
            }
            for v in visitors
        ]

    def request_visit(self, student_id: str, data: dict) -> dict:
        student = self.db.execute(select(Student).where(Student.id == student_id)).scalar_one_or_none()
        if not student:
            raise ValueError("Student not found")
        room_number = "UNASSIGNED"

        visitor = Visitor(
            name=data["name"],
            phone=data["phone"],
            purpose=data["purpose"],
            studentId=student.id,
            roomNumber=room_number,
            status=VisitorStatusEnum.PENDING,
            requestedAt=datetime.utcnow(),
        )
        self.db.add(visitor)
        self.db.commit()
        self.db.refresh(visitor)

        student_name = self.db.execute(
            select(User.name).join(Student, Student.userId == User.id).where(Student.id == student.id)
        ).scalar_one()

        return {
            "id": visitor.id,
            "name": visitor.name,
            "phone": visitor.phone,
            "purpose": visitor.purpose,
            "studentId": visitor.studentId,
            "studentName": student_name,
            "roomNumber": visitor.roomNumber,
            "status": visitor.status.value if hasattr(visitor.status, "value") else str(visitor.status),
            "requestedAt": visitor.requestedAt,
            "approvedAt": visitor.approvedAt,
            "approvedBy": visitor.approvedBy,
            "rejectionReason": visitor.rejectionReason,
            "entryTime": visitor.entryTime,
            "exitTime": visitor.exitTime,
            "createdAt": visitor.createdAt,
        }

    def admin_decide(self, visitor_id: str, status_value: str, approved_by: str, rejection_reason: Optional[str] = None) -> dict:
        if status_value not in ["APPROVED", "REJECTED"]:
            raise ValueError("Invalid status")
        visitor = self.db.execute(select(Visitor).where(Visitor.id == visitor_id)).scalar_one_or_none()
        if not visitor:
            raise ValueError("Visitor not found")
        visitor.status = VisitorStatusEnum(status_value)
        visitor.approvedAt = datetime.utcnow()
        visitor.approvedBy = approved_by
        visitor.rejectionReason = None
        if status_value == "REJECTED":
            visitor.rejectionReason = rejection_reason or "Rejected"
        self.db.commit()
        self.db.refresh(visitor)
        return {
            "id": visitor.id,
            "name": visitor.name,
            "phone": visitor.phone,
            "purpose": visitor.purpose,
            "studentId": visitor.studentId,
            "roomNumber": visitor.roomNumber,
            "status": visitor.status.value if hasattr(visitor.status, "value") else str(visitor.status),
            "requestedAt": visitor.requestedAt,
            "approvedAt": visitor.approvedAt,
            "approvedBy": visitor.approvedBy,
            "rejectionReason": visitor.rejectionReason,
            "entryTime": visitor.entryTime,
            "exitTime": visitor.exitTime,
            "createdAt": visitor.createdAt,
        }

