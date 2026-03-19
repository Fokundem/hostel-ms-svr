from prisma import Prisma
from typing import List, Optional
from datetime import datetime

from utils.exceptions import UnauthorizedException


class ComplaintService:
    def __init__(self, db: Prisma):
        self.db = db

    async def create_complaint(self, student_id: str, data: dict) -> dict:
        c = await self.db.complaint.create(
            data={
                "studentId": student_id,
                "title": data["title"],
                "description": data["description"],
                "category": data.get("category", "OTHER").upper(),
                "priority": data.get("priority", "MEDIUM").upper(),
                "status": "PENDING",
            }
        )
        return {
            "id": c.id,
            "studentId": c.studentId,
            "title": c.title,
            "description": c.description,
            "category": c.category,
            "priority": c.priority,
            "status": c.status,
            "adminResponse": c.adminResponse,
            "resolvedAt": c.resolvedAt,
            "createdAt": c.createdAt,
            "updatedAt": c.updatedAt,
        }

    async def list_all(self, status: Optional[str] = None) -> List[dict]:
        filters = {}
        if status:
            filters["status"] = status.upper()

        complaints = await self.db.complaint.find_many(
            where=filters,
            include={"student": {"include": {"user": True, "room": True}}},
            order={"createdAt": "desc"},
        )

        result = []
        for c in complaints:
            result.append(
                {
                    "id": c.id,
                    "studentId": c.studentId,
                    "studentName": c.student.user.name,
                    "roomNumber": c.student.room.roomNumber if c.student.room else None,
                    "title": c.title,
                    "description": c.description,
                    "category": c.category,
                    "priority": c.priority,
                    "status": c.status,
                    "adminResponse": c.adminResponse,
                    "resolvedAt": c.resolvedAt,
                    "createdAt": c.createdAt,
                    "updatedAt": c.updatedAt,
                }
            )
        return result

    async def list_for_student(self, student_id: str) -> List[dict]:
        complaints = await self.db.complaint.find_many(
            where={"studentId": student_id},
            order={"createdAt": "desc"},
        )
        return [
            {
                "id": c.id,
                "studentId": c.studentId,
                "title": c.title,
                "description": c.description,
                "category": c.category,
                "priority": c.priority,
                "status": c.status,
                "adminResponse": c.adminResponse,
                "resolvedAt": c.resolvedAt,
                "createdAt": c.createdAt,
                "updatedAt": c.updatedAt,
            }
            for c in complaints
        ]

    async def admin_update(self, complaint_id: str, data: dict) -> dict:
        update_data = {}
        if data.get("status") is not None:
            update_data["status"] = data["status"].upper()
            if update_data["status"] == "RESOLVED":
                update_data["resolvedAt"] = datetime.utcnow()
        if data.get("priority") is not None:
            update_data["priority"] = data["priority"].upper()
        if data.get("adminResponse") is not None:
            update_data["adminResponse"] = data["adminResponse"]

        c = await self.db.complaint.update(
            where={"id": complaint_id},
            data=update_data,
        )
        return {
            "id": c.id,
            "studentId": c.studentId,
            "title": c.title,
            "description": c.description,
            "category": c.category,
            "priority": c.priority,
            "status": c.status,
            "adminResponse": c.adminResponse,
            "resolvedAt": c.resolvedAt,
            "createdAt": c.createdAt,
            "updatedAt": c.updatedAt,
        }

