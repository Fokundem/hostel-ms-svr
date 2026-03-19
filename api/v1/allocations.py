from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from database import get_db
from services.allocation import AllocationService
from services.notification import NotificationService
from schemas.room import RoomAllocationResponse, RoomAllocationDetailResponse, RoomAllocationCreate, StudentAllocationResponse
from utils.dependencies import get_current_user, get_current_admin, get_current_student
from models import Student
from typing import Optional, List

router = APIRouter(prefix="/allocations", tags=["Room Allocations"])


def _get_student_by_user_id(db: Session, user_id: str):
    return db.execute(select(Student).where(Student.userId == user_id)).scalar_one_or_none()


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def request_room(
    allocation_data: RoomAllocationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_student)
):
    """Student requests a room"""
    try:
        student = _get_student_by_user_id(db, current_user.id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

        service = AllocationService(db)
        allocation = service.request_room(student.id, current_user.id, allocation_data.roomId)
        NotificationService(db).create_for_roles(
            roles=["ADMIN", "HOSTEL_MANAGER"],
            title="New room allocation request",
            message=f"{current_user.name} requested a room allocation.",
            type_value="SYSTEM",
            data={"link": "/admin/allocations", "allocationId": allocation["id"]},
        )
        return {"message": "Room request submitted successfully", "allocation": allocation}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/student/mine", response_model=Optional[StudentAllocationResponse])
def get_my_allocation(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_student)
):
    """Get current student's room allocation"""
    try:
        student = _get_student_by_user_id(db, current_user.id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

        service = AllocationService(db)
        allocation = service.get_student_allocation(student.id)
        return allocation
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=List[RoomAllocationDetailResponse])
def get_allocations(
    filter_status: Optional[str] = Query(None, alias="status"),
    hostel_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get all room allocations (admin only)"""
    try:
        service = AllocationService(db)
        allocations = service.get_all_allocations(status=filter_status, hostel_id=hostel_id)
        return allocations
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/pending", response_model=List[dict])
def get_pending_allocations(
    hostel_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get pending allocation requests (admin/hostel manager)"""
    try:
        service = AllocationService(db)
        allocations = service.get_pending_allocations(hostel_id=hostel_id)
        return allocations
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{allocation_id}", response_model=RoomAllocationDetailResponse)
def get_allocation_details(
    allocation_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get allocation details (admin only)"""
    try:
        service = AllocationService(db)
        allocation = service.get_allocation_by_id(allocation_id)
        if not allocation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
        return allocation
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{allocation_id}/approve", response_model=dict)
def approve_allocation(
    allocation_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Approve a room allocation (admin only)"""
    try:
        service = AllocationService(db)
        allocation = service.approve_allocation(allocation_id, current_user.id)
        student = db.execute(
            select(Student)
            .where(Student.id == allocation["studentId"])
            .options(joinedload(Student.room))
        ).unique().scalar_one_or_none()
        if student:
            NotificationService(db).create_for_user(
                user_id=student.userId,
                title="Room allocation approved",
                message=f"Your room request was approved. Assigned room: {student.room.roomNumber if student.room else ''}.",
                type_value="ROOM_APPROVED",
                data={"link": "/student/room", "allocationId": allocation["id"]},
            )
        return {"message": "Room allocation approved successfully", "allocation": allocation}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{allocation_id}/reject", response_model=dict)
def reject_allocation(
    allocation_id: str,
    reason: str = Query(..., description="Reason for rejection"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Reject a room allocation (admin only)"""
    try:
        service = AllocationService(db)
        allocation = service.reject_allocation(allocation_id, current_user.id, reason)
        student = db.execute(select(Student).where(Student.id == allocation["studentId"])).scalar_one_or_none()
        if student:
            NotificationService(db).create_for_user(
                user_id=student.userId,
                title="Room allocation rejected",
                message=f"Your room request was rejected. Reason: {allocation.get('rejectionReason') or reason}.",
                type_value="ROOM_REJECTED",
                data={"link": "/student/room", "allocationId": allocation["id"]},
            )
        return {"message": "Room allocation rejected", "allocation": allocation}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
