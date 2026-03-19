from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc
from datetime import datetime
from typing import Optional, List

from utils.exceptions import AllocationNotFoundException, RoomNotFoundException, RoomFullException
from models import Room, RoomAllocation, Student, RoomStatusEnum, AllocationStatusEnum


class AllocationService:
    def __init__(self, db: Session):
        self.db = db

    def request_room(self, student_id: str, user_id: str, room_id: str) -> dict:
        room = self.db.execute(select(Room).where(Room.id == room_id)).scalar_one_or_none()
        if not room:
            raise RoomNotFoundException()
        if room.status != RoomStatusEnum.AVAILABLE:
            status_val = room.status.value if hasattr(room.status, "value") else str(room.status)
            raise RoomFullException(f"Room is {status_val.lower()}")

        existing = self.db.execute(
            select(RoomAllocation).where(
                RoomAllocation.studentId == student_id,
                RoomAllocation.status == AllocationStatusEnum.PENDING,
            )
        ).scalar_one_or_none()
        if existing:
            raise ValueError("You already have a pending room allocation request")

        allocation = RoomAllocation(
            studentId=student_id,
            userId=user_id,
            roomId=room_id,
            status=AllocationStatusEnum.PENDING,
        )
        self.db.add(allocation)
        self.db.commit()
        self.db.refresh(allocation)
        return {
            "id": allocation.id,
            "studentId": allocation.studentId,
            "roomId": allocation.roomId,
            "status": allocation.status.value if hasattr(allocation.status, "value") else str(allocation.status),
            "requestedAt": allocation.requestedAt.isoformat() if allocation.requestedAt else None,
        }

    def get_student_allocation(self, student_id: str) -> Optional[dict]:
        allocation = (
            self.db.execute(
                select(RoomAllocation)
                .where(RoomAllocation.studentId == student_id)
                .options(joinedload(RoomAllocation.room))
                .order_by(desc(RoomAllocation.requestedAt))
                .limit(1)
            )
            .scalars()
            .first()
        )
        if not allocation:
            return None

        room = allocation.room
        status_val = allocation.status.value if hasattr(allocation.status, "value") else str(allocation.status)
        return {
            "id": allocation.id,
            "studentId": allocation.studentId,
            "roomId": allocation.roomId,
            "status": status_val,
            "requestedAt": allocation.requestedAt.isoformat() if allocation.requestedAt else None,
            "approvedAt": allocation.approvedAt.isoformat() if allocation.approvedAt else None,
            "room": {
                "id": room.id,
                "roomNumber": room.roomNumber,
                "floor": room.floor,
                "block": room.block,
                "capacity": room.capacity,
                "occupied": room.occupied,
                "status": room.status.value if hasattr(room.status, "value") else str(room.status),
                "amenities": room.amenities or [],
                "price": room.price,
                "createdAt": room.createdAt.isoformat() if room.createdAt else None,
            },
        }

    def get_all_allocations(self, status: Optional[str] = None, hostel_id: Optional[str] = None) -> List[dict]:
        q = select(RoomAllocation).options(
            joinedload(RoomAllocation.student).joinedload(Student.user),
            joinedload(RoomAllocation.room),
        ).order_by(desc(RoomAllocation.requestedAt))
        if status:
            q = q.where(RoomAllocation.status == AllocationStatusEnum(status))
        result = self.db.execute(q).unique().scalars().all()

        admin_ids = {alloc.approvedBy for alloc in result if alloc.approvedBy}
        admin_names = {}
        if admin_ids:
            from models import User
            admins = self.db.execute(select(User.id, User.name).where(User.id.in_(admin_ids))).all()
            admin_names = {a.id: a.name for a in admins}

        out = []
        for alloc in result:
            if hostel_id and alloc.room.hostelId != hostel_id:
                continue
            status_val = alloc.status.value if hasattr(alloc.status, "value") else str(alloc.status)
            room_status = alloc.room.status.value if hasattr(alloc.room.status, "value") else str(alloc.room.status)
            # Build full student response
            student = alloc.student
            user = student.user
            student_resp = {
                "id": student.id,
                "userId": student.userId,
                "name": user.name,
                "email": user.email,
                "matricule": student.matricule,
                "department": student.department,
                "level": student.level,
                "phone": user.phone,
                "guardianContact": student.guardianContact,
                "roomId": student.roomId,
                "assignedRoom": student.assignedRoom if hasattr(student, "assignedRoom") else None,
                "role": user.role.value if hasattr(user.role, "value") else str(user.role),
                "status": user.status.value if hasattr(user.status, "value") else str(user.status),
                "createdAt": user.createdAt.isoformat() if user.createdAt else None,
            }
            # Build full room response
            room = alloc.room
            room_resp = {
                "id": room.id,
                "roomNumber": room.roomNumber,
                "floor": room.floor,
                "block": room.block,
                "hostelId": room.hostelId,
                "capacity": room.capacity,
                "occupied": room.occupied,
                "status": room_status,
                "amenities": room.amenities if room.amenities is not None else [],
                "price": room.price,
                "createdAt": room.createdAt.isoformat() if room.createdAt else None,
            }
            out.append({
                "id": alloc.id,
                "studentId": alloc.studentId,
                "roomId": alloc.roomId,
                "status": status_val,
                "requestedAt": alloc.requestedAt.isoformat() if alloc.requestedAt else None,
                "approvedAt": alloc.approvedAt.isoformat() if alloc.approvedAt else None,
                "approvedBy": alloc.approvedBy,
                "approvedByName": admin_names.get(alloc.approvedBy) if alloc.approvedBy else None,
                "rejectionReason": alloc.rejectionReason,
                "student": student_resp,
                "room": room_resp,
            })
        return out

    def approve_allocation(self, allocation_id: str, approved_by: str) -> dict:
        allocation = (
            self.db.execute(
                select(RoomAllocation)
                .where(RoomAllocation.id == allocation_id)
                .options(joinedload(RoomAllocation.room), joinedload(RoomAllocation.student))
            )
            .unique()
            .scalar_one_or_none()
        )
        if not allocation:
            raise AllocationNotFoundException()
        if allocation.status != AllocationStatusEnum.PENDING:
            raise ValueError("Allocation is already processed")
        if allocation.room.status != RoomStatusEnum.AVAILABLE:
            raise RoomFullException("Room is no longer available")

        allocation.status = AllocationStatusEnum.APPROVED
        allocation.approvedAt = datetime.utcnow()
        allocation.approvedBy = approved_by

        allocation.student.roomId = allocation.roomId
        room = allocation.room
        room.occupied = (room.occupied or 0) + 1
        room.status = RoomStatusEnum.FULL if room.occupied >= room.capacity else RoomStatusEnum.AVAILABLE

        self.db.commit()
        self.db.refresh(allocation)

        return {
            "id": allocation.id,
            "studentId": allocation.studentId,
            "roomId": allocation.roomId,
            "status": allocation.status.value,
            "approvedAt": allocation.approvedAt.isoformat(),
            "approvedBy": allocation.approvedBy,
        }

    def reject_allocation(self, allocation_id: str, approved_by: str, reason: str) -> dict:
        allocation = self.db.execute(
            select(RoomAllocation).where(RoomAllocation.id == allocation_id)
        ).scalar_one_or_none()
        if not allocation:
            raise AllocationNotFoundException()
        if allocation.status != AllocationStatusEnum.PENDING:
            raise ValueError("Allocation is already processed")

        allocation.status = AllocationStatusEnum.REJECTED
        allocation.approvedBy = approved_by
        allocation.rejectionReason = reason
        self.db.commit()
        self.db.refresh(allocation)

        return {
            "id": allocation.id,
            "studentId": allocation.studentId,
            "roomId": allocation.roomId,
            "status": allocation.status.value,
            "rejectionReason": allocation.rejectionReason,
        }

    def get_allocation_by_id(self, allocation_id: str) -> Optional[dict]:
        allocation = (
            self.db.execute(
                select(RoomAllocation)
                .where(RoomAllocation.id == allocation_id)
                .options(
                    joinedload(RoomAllocation.student),
                    joinedload(RoomAllocation.room),
                )
            )
            .unique()
            .scalar_one_or_none()
        )
        if not allocation:
            return None
            
        admin_name = None
        if allocation.approvedBy:
            from models import User
            admin = self.db.execute(select(User.name).where(User.id == allocation.approvedBy)).scalar_one_or_none()
            if admin:
                admin_name = admin

        room = allocation.room
        status_val = allocation.status.value if hasattr(allocation.status, "value") else str(allocation.status)
        room_status = room.status.value if hasattr(room.status, "value") else str(room.status)
        return {
            "id": allocation.id,
            "studentId": allocation.studentId,
            "roomId": allocation.roomId,
            "status": status_val,
            "requestedAt": allocation.requestedAt,
            "approvedAt": allocation.approvedAt,
            "approvedBy": allocation.approvedBy,
            "approvedByName": admin_name,
            "rejectionReason": allocation.rejectionReason,
            "student": {
                "id": allocation.student.id,
                "userId": allocation.student.userId,
                "matricule": allocation.student.matricule,
                "department": allocation.student.department,
                "level": allocation.student.level,
            },
            "room": {
                "id": room.id,
                "roomNumber": room.roomNumber,
                "floor": room.floor,
                "block": room.block,
                "capacity": room.capacity,
                "occupied": room.occupied,
                "status": room_status,
                "amenities": room.amenities or [],
                "price": room.price,
                "createdAt": room.createdAt.isoformat() if room.createdAt else None,
            },
        }

    def get_pending_allocations(self, hostel_id: Optional[str] = None) -> List[dict]:
        result = self.db.execute(
            select(RoomAllocation)
            .where(RoomAllocation.status == AllocationStatusEnum.PENDING)
            .options(
                joinedload(RoomAllocation.student).joinedload(Student.user),
                joinedload(RoomAllocation.room),
            )
            .order_by(RoomAllocation.requestedAt)
        ).unique().scalars().all()

        out = []
        for alloc in result:
            if hostel_id and alloc.room.hostelId != hostel_id:
                continue
            out.append({
                "id": alloc.id,
                "studentId": alloc.studentId,
                "studentName": alloc.student.user.name,
                "studentEmail": alloc.student.user.email,
                "matricule": alloc.student.matricule,
                "department": alloc.student.department,
                "level": alloc.student.level,
                "roomId": alloc.roomId,
                "roomNumber": alloc.room.roomNumber,
                "floor": alloc.room.floor,
                "block": alloc.room.block,
                "requestedAt": alloc.requestedAt.isoformat() if alloc.requestedAt else None,
            })
        return out
