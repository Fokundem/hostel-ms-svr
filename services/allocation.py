from prisma import Prisma
from utils.exceptions import AllocationNotFoundException, RoomNotFoundException, RoomFullException
from schemas.room import RoomAllocationCreate, RoomAllocationUpdateStatus
from datetime import datetime
from typing import Optional, List


class AllocationService:
    def __init__(self, db: Prisma):
        self.db = db

    async def request_room(self, student_id: str, user_id: str, room_id: str) -> dict:
        """Student requests a room"""
        # Check if room exists
        room = await self.db.room.find_unique(where={"id": room_id})
        if not room:
            raise RoomNotFoundException()
        
        # Check if room is available
        if room.status != "AVAILABLE":
            raise RoomFullException(f"Room is {room.status.lower()}")
        
        # Check if student already has pending allocation
        existing = await self.db.roomallocation.find_first(
            where={
                "studentId": student_id,
                "status": "PENDING"
            }
        )
        if existing:
            raise ValueError("You already have a pending room allocation request")
        
        # Create allocation request
        allocation = await self.db.roomallocation.create(
            data={
                "studentId": student_id,
                "userId": user_id,
                "roomId": room_id,
                "status": "PENDING",
            }
        )
        
        return {
            "id": allocation.id,
            "studentId": allocation.studentId,
            "roomId": allocation.roomId,
            "status": allocation.status,
            "requestedAt": allocation.requestedAt.isoformat(),
        }

    async def get_student_allocation(self, student_id: str) -> Optional[dict]:
        """Get student's room allocation"""
        allocation = await self.db.roomallocation.find_first(
            where={"studentId": student_id},
            order={"requestedAt": "desc"},
            include={"room": True}
        )
        
        if not allocation:
            return None
        
        return {
            "id": allocation.id,
            "studentId": allocation.studentId,
            "roomId": allocation.roomId,
            "status": allocation.status,
            "requestedAt": allocation.requestedAt.isoformat(),
            "approvedAt": allocation.approvedAt.isoformat() if allocation.approvedAt else None,
            "room": {
                "id": allocation.room.id,
                "roomNumber": allocation.room.roomNumber,
                "floor": allocation.room.floor,
                "block": allocation.room.block,
                "capacity": allocation.room.capacity,
                "occupied": allocation.room.occupied,
                "status": allocation.room.status,
                "amenities": allocation.room.amenities,
                "price": allocation.room.price,
                "createdAt": allocation.room.createdAt.isoformat(),
            }
        }

    async def get_all_allocations(self, status: Optional[str] = None, hostel_id: Optional[str] = None) -> List[dict]:
        """Get all room allocations (admin view), optionally filtered by status and hostel"""
        filters = {}
        if status:
            filters["status"] = status
        
        allocations = await self.db.roomallocation.find_many(
            where=filters,
            include={"student": True, "room": True},
            order={"requestedAt": "desc"}
        )
        
        result = []
        for alloc in allocations:
            # Filter by hostel if specified
            if hostel_id and alloc.room.hostelId != hostel_id:
                continue
            
            result.append({
                "id": alloc.id,
                "studentId": alloc.studentId,
                "studentName": alloc.student.user.name,
                "roomId": alloc.roomId,
                "roomNumber": alloc.room.roomNumber,
                "floor": alloc.room.floor,
                "status": alloc.status,
                "requestedAt": alloc.requestedAt.isoformat(),
                "approvedAt": alloc.approvedAt.isoformat() if alloc.approvedAt else None,
                "approvedBy": alloc.approvedBy,
                "rejectionReason": alloc.rejectionReason,
                "room": {
                    "id": alloc.room.id,
                    "roomNumber": alloc.room.roomNumber,
                    "floor": alloc.room.floor,
                    "block": alloc.room.block,
                    "capacity": alloc.room.capacity,
                    "occupied": alloc.room.occupied,
                    "price": alloc.room.price,
                }
            })
        
        return result

    async def approve_allocation(self, allocation_id: str, approved_by: str) -> dict:
        """Admin approves a room allocation"""
        allocation = await self.db.roomallocation.find_unique(
            where={"id": allocation_id},
            include={"room": True, "student": True}
        )
        
        if not allocation:
            raise AllocationNotFoundException()
        
        if allocation.status != "PENDING":
            raise ValueError(f"Allocation is already {allocation.status.lower()}")
        
        # Check if room is still available
        if allocation.room.status != "AVAILABLE":
            raise RoomFullException("Room is no longer available")
        
        # Update allocation status
        updated_allocation = await self.db.roomallocation.update(
            where={"id": allocation_id},
            data={
                "status": "APPROVED",
                "approvedAt": datetime.utcnow(),
                "approvedBy": approved_by,
            },
            include={"room": True}
        )
        
        # Update student room assignment
        await self.db.student.update(
            where={"id": allocation.studentId},
            data={"roomId": allocation.roomId}
        )
        
        # Update room occupied count and status
        new_occupied = allocation.room.occupied + 1
        new_status = "FULL" if new_occupied >= allocation.room.capacity else "AVAILABLE"
        
        await self.db.room.update(
            where={"id": allocation.roomId},
            data={
                "occupied": new_occupied,
                "status": new_status,
            }
        )
        
        return {
            "id": updated_allocation.id,
            "studentId": updated_allocation.studentId,
            "roomId": updated_allocation.roomId,
            "status": updated_allocation.status,
            "approvedAt": updated_allocation.approvedAt.isoformat(),
            "approvedBy": updated_allocation.approvedBy,
        }

    async def reject_allocation(self, allocation_id: str, approved_by: str, reason: str) -> dict:
        """Admin rejects a room allocation"""
        allocation = await self.db.roomallocation.find_unique(where={"id": allocation_id})
        
        if not allocation:
            raise AllocationNotFoundException()
        
        if allocation.status != "PENDING":
            raise ValueError(f"Allocation is already {allocation.status.lower()}")
        
        # Update allocation status
        updated_allocation = await self.db.roomallocation.update(
            where={"id": allocation_id},
            data={
                "status": "REJECTED",
                "approvedBy": approved_by,
                "rejectionReason": reason,
            }
        )
        
        return {
            "id": updated_allocation.id,
            "studentId": updated_allocation.studentId,
            "roomId": updated_allocation.roomId,
            "status": updated_allocation.status,
            "rejectionReason": updated_allocation.rejectionReason,
        }

    async def get_pending_allocations(self, hostel_id: Optional[str] = None) -> List[dict]:
        """Get pending allocation requests for admin/hostel manager"""
        allocations = await self.db.roomallocation.find_many(
            where={"status": "PENDING"},
            include={"student": True, "room": True},
            order={"requestedAt": "asc"}
        )
        
        result = []
        for alloc in allocations:
            # Filter by hostel if specified
            if hostel_id and alloc.room.hostelId != hostel_id:
                continue
            
            result.append({
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
                "requestedAt": alloc.requestedAt.isoformat(),
            })
        
        return result
