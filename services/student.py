from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc
from typing import List, Optional

from utils.security import hash_password
from utils.exceptions import UserAlreadyExistsException, UserNotFoundException
from models import User, Student, RoleEnum, UserStatusEnum, Room, RoomStatusEnum


def _student_to_dict(s: Student) -> dict:
    role_val = s.user.role.value if hasattr(s.user.role, "value") else str(s.user.role)
    status_val = s.user.status.value if hasattr(s.user.status, "value") else str(s.user.status)
    return {
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
        "role": role_val,
        "status": status_val,
        "createdAt": s.createdAt,
    }


class StudentService:
    def __init__(self, db: Session):
        self.db = db

    def list_students(self) -> List[dict]:
        result = self.db.execute(
            select(Student)
            .options(joinedload(Student.user), joinedload(Student.room))
            .order_by(desc(Student.createdAt))
        )
        students = result.unique().scalars().all()
        return [_student_to_dict(s) for s in students]

    def create_student(self, data: dict) -> dict:
        existing_user = self.db.execute(select(User).where(User.email == data["email"])).scalar_one_or_none()
        if existing_user:
            raise UserAlreadyExistsException()

        existing_student = self.db.execute(
            select(Student).where(Student.matricule == data["matricule"])
        ).scalar_one_or_none()
        if existing_student:
            raise ValueError(f"Student with matricule {data['matricule']} already exists")

        user = User(
            email=data["email"],
            password=hash_password(data["password"]),
            name=data["name"],
            phone=data.get("phone"),
            role=RoleEnum.STUDENT,
            status=UserStatusEnum.ACTIVE,
        )
        self.db.add(user)
        self.db.flush()

        student = Student(
            userId=user.id,
            matricule=data["matricule"],
            department=data["department"],
            level=data["level"],
            guardianContact=data.get("guardianContact"),
        )
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        self.db.refresh(user)
        return _student_to_dict(student)

    def update_student(self, student_id: str, data: dict) -> dict:
        student = self.db.execute(
            select(Student)
            .where(Student.id == student_id)
            .options(joinedload(Student.user), joinedload(Student.room))
        ).unique().scalar_one_or_none()
        if not student:
            raise UserNotFoundException("Student not found")

        if data.get("name") is not None:
            student.user.name = data["name"]
        if data.get("phone") is not None:
            student.user.phone = data["phone"]
        if data.get("status") is not None:
            student.user.status = UserStatusEnum(data["status"].upper())
        if data.get("role") is not None:
            student.user.role = RoleEnum(data["role"].upper())
        for field in ["guardianContact", "department", "level", "roomId"]:
            if data.get(field) is not None:
                setattr(student, field, data[field])

        self.db.commit()
        self.db.refresh(student)
        return _student_to_dict(student)

    def delete_student(self, student_id: str) -> None:
        student = self.db.execute(
            select(Student).where(Student.id == student_id).options(joinedload(Student.room))
        ).unique().scalar_one_or_none()
        if not student:
            raise UserNotFoundException("Student not found")
        # If student has a room, decrement occupied count and update status
        if student.roomId and student.room:
            room = student.room
            room.occupied = max(0, (room.occupied or 0) - 1)
            room.status = RoomStatusEnum.AVAILABLE if (room.occupied or 0) < room.capacity else RoomStatusEnum.FULL
            
        from models import Payment, Complaint, Visitor, RoomAllocation, Notification
        # Delete related records explicitly to prevent IntegrityError 
        self.db.execute(Payment.__table__.delete().where(Payment.studentId == student_id))
        self.db.execute(Complaint.__table__.delete().where(Complaint.studentId == student_id))
        self.db.execute(Visitor.__table__.delete().where(Visitor.studentId == student_id))
        self.db.execute(RoomAllocation.__table__.delete().where(RoomAllocation.studentId == student_id))

        user_id = student.userId
        self.db.delete(student)
        self.db.execute(Notification.__table__.delete().where(Notification.userId == user_id))
        self.db.execute(User.__table__.delete().where(User.id == user_id))
        self.db.commit()
