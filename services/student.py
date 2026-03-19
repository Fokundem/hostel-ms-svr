from prisma import Prisma
from typing import List, Optional

from utils.security import hash_password
from utils.exceptions import UserAlreadyExistsException, UserNotFoundException


class StudentService:
    def __init__(self, db: Prisma):
        self.db = db

    async def list_students(self) -> List[dict]:
        students = await self.db.student.find_many(
            include={"user": True, "room": True},
            order={"createdAt": "desc"},
        )

        result: List[dict] = []
        for s in students:
            result.append(
                {
                    "id": s.id,
                    "userId": s.userId,
                    "name": s.user.name,
                    "email": s.user.email,
                    "matricule": s.matricule,
                    "department": s.department,
                    "level": s.level,
                    "phone": s.user.phone,
                    "guardianContact": s.guardianContact,
                    "roomId": s.roomId,
                    "assignedRoom": s.room.roomNumber if s.room else None,
                    "role": s.user.role,
                    "status": s.user.status,
                    "createdAt": s.createdAt,
                }
            )
        return result

    async def create_student(self, data: dict) -> dict:
        existing_user = await self.db.user.find_unique(where={"email": data["email"]})
        if existing_user:
            raise UserAlreadyExistsException()

        existing_student = await self.db.student.find_unique(where={"matricule": data["matricule"]})
        if existing_student:
            raise ValueError(f"Student with matricule {data['matricule']} already exists")

        user = await self.db.user.create(
            data={
                "email": data["email"],
                "password": hash_password(data["password"]),
                "name": data["name"],
                "phone": data.get("phone"),
                "role": "STUDENT",
                "status": "ACTIVE",
            }
        )

        student = await self.db.student.create(
            data={
                "userId": user.id,
                "matricule": data["matricule"],
                "department": data["department"],
                "level": data["level"],
                "guardianContact": data.get("guardianContact"),
            },
            include={"user": True, "room": True},
        )

        return {
            "id": student.id,
            "userId": student.userId,
            "name": student.user.name,
            "email": student.user.email,
            "matricule": student.matricule,
            "department": student.department,
            "level": student.level,
            "phone": student.user.phone,
            "guardianContact": student.guardianContact,
            "roomId": student.roomId,
            "assignedRoom": student.room.roomNumber if student.room else None,
            "role": student.user.role,
            "status": student.user.status,
            "createdAt": student.createdAt,
        }

    async def update_student(self, student_id: str, data: dict) -> dict:
        student = await self.db.student.find_unique(where={"id": student_id}, include={"user": True, "room": True})
        if not student:
            raise UserNotFoundException("Student not found")

        user_updates = {}
        if data.get("name") is not None:
            user_updates["name"] = data["name"]
        if data.get("phone") is not None:
            user_updates["phone"] = data["phone"]
        if data.get("status") is not None:
            user_updates["status"] = data["status"].upper()
        if data.get("role") is not None:
            user_updates["role"] = data["role"].upper()

        if user_updates:
            await self.db.user.update(where={"id": student.userId}, data=user_updates)

        student_updates = {}
        for field in ["guardianContact", "department", "level", "roomId"]:
            if data.get(field) is not None:
                student_updates[field] = data[field]

        if student_updates:
            await self.db.student.update(where={"id": student_id}, data=student_updates)

        updated = await self.db.student.find_unique(where={"id": student_id}, include={"user": True, "room": True})
        return {
            "id": updated.id,
            "userId": updated.userId,
            "name": updated.user.name,
            "email": updated.user.email,
            "matricule": updated.matricule,
            "department": updated.department,
            "level": updated.level,
            "phone": updated.user.phone,
            "guardianContact": updated.guardianContact,
            "roomId": updated.roomId,
            "assignedRoom": updated.room.roomNumber if updated.room else None,
            "role": updated.user.role,
            "status": updated.user.status,
            "createdAt": updated.createdAt,
        }

    async def delete_student(self, student_id: str) -> None:
        student = await self.db.student.find_unique(where={"id": student_id})
        if not student:
            raise UserNotFoundException("Student not found")
        await self.db.user.delete(where={"id": student.userId})

