from fastapi import APIRouter, Depends, HTTPException, status, Query
from database import get_db
from services.allocation import AllocationService
from schemas.room import RoomAllocationResponse, RoomAllocationDetailResponse, RoomAllocationCreate, StudentAllocationResponse
from utils.dependencies import get_current_user, get_current_admin, get_current_student
from prisma import Prisma
from prisma.errors import PrismaError
from typing import Optional, List
from services.notification import NotificationService

router = APIRouter(prefix="/allocations", tags=["Room Allocations"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def request_room(
    allocation_data: RoomAllocationCreate,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_student)
):
    """Student requests a room"""
    try:
        # Get student profile
        student = await db.student.find_unique(where={"userId": current_user.id})
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
        
        service = AllocationService(db)
        allocation = await service.request_room(student.id, current_user.id, allocation_data.roomId)
        await NotificationService(db).create_for_roles(
            roles=["ADMIN", "HOSTEL_MANAGER"],
            title="New room allocation request",
            message=f"{current_user.name} requested a room allocation.",
            type_value="SYSTEM",
            data={"link": "/admin/allocations", "allocationId": allocation["id"]},
        )
        
        return {
            "message": "Room request submitted successfully",
            "allocation": allocation
        }
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PrismaError as e:
        # Most common: unique constraint, missing FK, etc.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/student/mine", response_model=Optional[StudentAllocationResponse])
async def get_my_allocation(
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_student)
):
    """Get current student's room allocation"""
    try:
        # Get student profile
        student = await db.student.find_unique(where={"userId": current_user.id})
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
        
        service = AllocationService(db)
        allocation = await service.get_student_allocation(student.id)
        
        return allocation
    except HTTPException as e:
        raise e
    except PrismaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=List[RoomAllocationDetailResponse])
async def get_allocations(
    status: Optional[str] = Query(None),
    hostel_id: Optional[str] = Query(None),
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get all room allocations (admin only)"""
    try:
        service = AllocationService(db)
        allocations = await service.get_all_allocations(status=status, hostel_id=hostel_id)
        return allocations
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/pending", response_model=List[dict])
async def get_pending_allocations(
    hostel_id: Optional[str] = Query(None),
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get pending allocation requests (admin/hostel manager)"""
    try:
        service = AllocationService(db)
        allocations = await service.get_pending_allocations(hostel_id=hostel_id)
        return allocations
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{allocation_id}", response_model=RoomAllocationDetailResponse)
async def get_allocation_details(
    allocation_id: str,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get allocation details (admin only)"""
    try:
        allocation = await db.roomallocation.find_unique(
            where={"id": allocation_id},
            include={"student": True, "room": True}
        )
        
        if not allocation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
        
        return {
            "id": allocation.id,
            "studentId": allocation.studentId,
            "roomId": allocation.roomId,
            "status": allocation.status,
            "requestedAt": allocation.requestedAt,
            "approvedAt": allocation.approvedAt,
            "approvedBy": allocation.approvedBy,
            "rejectionReason": allocation.rejectionReason,
            "student": {
                "id": allocation.student.id,
                "userId": allocation.student.userId,
                "matricule": allocation.student.matricule,
                "department": allocation.student.department,
                "level": allocation.student.level,
            },
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
                "createdAt": allocation.room.createdAt,
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{allocation_id}/approve", response_model=dict)
async def approve_allocation(
    allocation_id: str,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Approve a room allocation (admin only)"""
    try:
        service = AllocationService(db)
        allocation = await service.approve_allocation(allocation_id, current_user.id)
        student = await db.student.find_unique(where={"id": allocation["studentId"]}, include={"user": True, "room": True})
        if student and student.user:
            await NotificationService(db).create_for_user(
                user_id=student.user.id,
                title="Room allocation approved",
                message=f"Your room request was approved. Assigned room: {student.room.roomNumber if student.room else ''}.",
                type_value="ROOM_APPROVED",
                data={"link": "/student/room", "allocationId": allocation["id"]},
            )
        
        return {
            "message": "Room allocation approved successfully",
            "allocation": allocation
        }
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{allocation_id}/reject", response_model=dict)
async def reject_allocation(
    allocation_id: str,
    reason: str = Query(..., description="Reason for rejection"),
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Reject a room allocation (admin only)"""
    try:
        service = AllocationService(db)
        allocation = await service.reject_allocation(allocation_id, current_user.id, reason)
        student = await db.student.find_unique(where={"id": allocation["studentId"]}, include={"user": True})
        if student and student.user:
            await NotificationService(db).create_for_user(
                user_id=student.user.id,
                title="Room allocation rejected",
                message=f"Your room request was rejected. Reason: {allocation.get('rejectionReason') or reason}.",
                type_value="ROOM_REJECTED",
                data={"link": "/student/room", "allocationId": allocation["id"]},
            )
        
        return {
            "message": "Room allocation rejected",
            "allocation": allocation
        }
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
