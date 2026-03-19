from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc
from datetime import datetime
from typing import List, Optional

from models import Complaint, Student, ComplaintStatusEnum, ComplaintCategoryEnum, ComplaintPriorityEnum


def _complaint_to_dict(c: Complaint, include_student: bool = False) -> dict:
    status_val = c.status.value if hasattr(c.status, "value") else str(c.status)
    category_val = c.category.value if hasattr(c.category, "value") else str(c.category)
    priority_val = c.priority.value if hasattr(c.priority, "value") else str(c.priority)
    out = {
        "id": c.id,
        "studentId": c.studentId,
        "title": c.title,
        "description": c.description,
        "category": category_val,
        "priority": priority_val,
        "status": status_val,
        "adminResponse": c.adminResponse,
        "resolvedAt": c.resolvedAt.isoformat() if c.resolvedAt else None,
        "createdAt": c.createdAt.isoformat() if c.createdAt else None,
        "updatedAt": c.updatedAt.isoformat() if c.updatedAt else None,
    }
    if include_student and c.student:
        out["studentName"] = c.student.user.name if c.student.user else None
        out["roomNumber"] = c.student.room.roomNumber if c.student.room else None
    return out


class ComplaintService:
    def __init__(self, db: Session):
        self.db = db

    def create_complaint(self, student_id: str, data: dict) -> dict:
        category = data.get("category", "OTHER")
        priority = data.get("priority", "MEDIUM")
        if isinstance(category, str):
            category = ComplaintCategoryEnum(category) if category in [e.value for e in ComplaintCategoryEnum] else ComplaintCategoryEnum.OTHER
        if isinstance(priority, str):
            priority = ComplaintPriorityEnum(priority) if priority in [e.value for e in ComplaintPriorityEnum] else ComplaintPriorityEnum.MEDIUM
        c = Complaint(
            studentId=student_id,
            title=data["title"],
            description=data["description"],
            category=category,
            priority=priority,
            status=ComplaintStatusEnum.PENDING,
        )
        self.db.add(c)
        self.db.commit()
        self.db.refresh(c)
        return _complaint_to_dict(c)

    def list_all(self, status: Optional[str] = None) -> List[dict]:
        q = select(Complaint).options(
            joinedload(Complaint.student).joinedload(Student.user),
            joinedload(Complaint.student).joinedload(Student.room),
        ).order_by(desc(Complaint.createdAt))
        if status:
            q = q.where(Complaint.status == ComplaintStatusEnum(status))
        complaints = self.db.execute(q).unique().scalars().all()
        return [_complaint_to_dict(c, include_student=True) for c in complaints]

    def list_for_student(self, student_id: str) -> List[dict]:
        complaints = self.db.execute(
            select(Complaint).where(Complaint.studentId == student_id).order_by(desc(Complaint.createdAt))
        ).scalars().all()
        return [_complaint_to_dict(c) for c in complaints]

    def admin_update(self, complaint_id: str, data: dict) -> dict:
        c = self.db.execute(select(Complaint).where(Complaint.id == complaint_id)).scalar_one_or_none()
        if not c:
            raise ValueError("Complaint not found")
        if data.get("status") is not None:
            s = data["status"]
            c.status = ComplaintStatusEnum(s) if isinstance(s, str) else s
            if c.status == ComplaintStatusEnum.RESOLVED:
                c.resolvedAt = datetime.utcnow()
        if data.get("priority") is not None:
            p = data["priority"]
            c.priority = ComplaintPriorityEnum(p) if isinstance(p, str) else p
        if data.get("adminResponse") is not None:
            c.adminResponse = data["adminResponse"]
        self.db.commit()
        self.db.refresh(c)
        return _complaint_to_dict(c)
