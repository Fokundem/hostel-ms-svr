from prisma import Prisma
from typing import List, Optional
from datetime import datetime


class VisitorService:
    def __init__(self, db: Prisma):
        self.db = db

    async def list_visitors(self, status: Optional[str] = None) -> List[dict]:
        filters = {}
        if status:
            filters["status"] = status.upper()

        visitors = await self.db.visitor.find_many(
            where=filters,
            include={"student": {"include": {"user": True, "room": True}}},
            order={"createdAt": "desc"},
        )

        result = []
        for v in visitors:
            result.append(
                {
                    "id": v.id,
                    "name": v.name,
                    "phone": v.phone,
                    "purpose": v.purpose,
                    "studentId": v.studentId,
                    "studentName": v.student.user.name,
                    "roomNumber": v.student.room.roomNumber if v.student.room else v.roomNumber,
                    "status": v.status,
                    "requestedAt": v.requestedAt,
                    "approvedAt": v.approvedAt,
                    "approvedBy": v.approvedBy,
                    "rejectionReason": v.rejectionReason,
                    "entryTime": v.entryTime,
                    "exitTime": v.exitTime,
                    "createdAt": v.createdAt,
                }
            )
        return result

    async def list_for_student(self, student_id: str) -> List[dict]:
        visitors = await self.db.visitor.find_many(
            where={"studentId": student_id},
            order={"createdAt": "desc"},
        )
        return [
            {
                "id": v.id,
                "name": v.name,
                "phone": v.phone,
                "purpose": v.purpose,
                "studentId": v.studentId,
                "roomNumber": v.roomNumber,
                "status": v.status,
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

    async def request_visit(self, student_id: str, data: dict) -> dict:
        student = await self.db.student.find_unique(
            where={"id": student_id},
            include={"room": True, "user": True},
        )
        if not student:
            raise ValueError("Student not found")
        room_number = student.room.roomNumber if student.room else "UNASSIGNED"

        visitor = await self.db.visitor.create(
            data={
                "name": data["name"],
                "phone": data["phone"],
                "purpose": data["purpose"],
                "studentId": student.id,
                "roomNumber": room_number,
                "status": "PENDING",
                "requestedAt": datetime.utcnow(),
            }
        )

        return {
            "id": visitor.id,
            "name": visitor.name,
            "phone": visitor.phone,
            "purpose": visitor.purpose,
            "studentId": visitor.studentId,
            "studentName": student.user.name,
            "roomNumber": visitor.roomNumber,
            "status": visitor.status,
            "requestedAt": visitor.requestedAt,
            "approvedAt": visitor.approvedAt,
            "approvedBy": visitor.approvedBy,
            "rejectionReason": visitor.rejectionReason,
            "entryTime": visitor.entryTime,
            "exitTime": visitor.exitTime,
            "createdAt": visitor.createdAt,
        }

    async def admin_decide(self, visitor_id: str, status_value: str, approved_by: str, rejection_reason: Optional[str] = None) -> dict:
        if status_value not in ["APPROVED", "REJECTED"]:
            raise ValueError("Invalid status")
        data = {
            "status": status_value,
            "approvedAt": datetime.utcnow(),
            "approvedBy": approved_by,
            "rejectionReason": None,
        }
        if status_value == "REJECTED":
            data["rejectionReason"] = rejection_reason or "Rejected"
        visitor = await self.db.visitor.update(where={"id": visitor_id}, data=data)
        return {
            "id": visitor.id,
            "name": visitor.name,
            "phone": visitor.phone,
            "purpose": visitor.purpose,
            "studentId": visitor.studentId,
            "roomNumber": visitor.roomNumber,
            "status": visitor.status,
            "requestedAt": visitor.requestedAt,
            "approvedAt": visitor.approvedAt,
            "approvedBy": visitor.approvedBy,
            "rejectionReason": visitor.rejectionReason,
            "entryTime": visitor.entryTime,
            "exitTime": visitor.exitTime,
            "createdAt": visitor.createdAt,
        }

