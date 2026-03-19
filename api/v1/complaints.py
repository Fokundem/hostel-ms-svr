from fastapi import APIRouter, Depends, HTTPException, status, Query
from prisma import Prisma
from typing import Optional

from database import get_db
from utils.dependencies import get_current_admin, get_current_student
from services.complaint import ComplaintService
from schemas.complaints import ComplaintCreate, ComplaintAdminUpdate
from services.notification import NotificationService


router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.get("", response_model=list[dict])
async def list_complaints(
    status: Optional[str] = Query(None),
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    service = ComplaintService(db)
    return await service.list_all(status=status)


@router.get("/student/mine", response_model=list[dict])
async def list_my_complaints(
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_student),
):
    student = await db.student.find_unique(where={"userId": current_user.id})
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    service = ComplaintService(db)
    return await service.list_for_student(student.id)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    payload: ComplaintCreate,
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_student),
):
    try:
        student = await db.student.find_unique(where={"userId": current_user.id})
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        service = ComplaintService(db)
        complaint = await service.create_complaint(student.id, payload.model_dump())
        await NotificationService(db).create_for_roles(
            roles=["ADMIN", "HOSTEL_MANAGER"],
            title="New complaint submitted",
            message=f"{current_user.name} submitted a complaint: {complaint['title']}.",
            type_value="COMPLAINT_UPDATE",
            data={"link": "/admin/complaints", "complaintId": complaint["id"]},
        )
        return {"message": "Complaint submitted successfully", "complaint": complaint}
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error submitting complaint")


@router.put("/{complaint_id}", response_model=dict)
async def admin_update_complaint(
    complaint_id: str,
    payload: ComplaintAdminUpdate,
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    try:
        service = ComplaintService(db)
        complaint = await service.admin_update(complaint_id, payload.model_dump(exclude_unset=True))
        student = await db.student.find_unique(where={"id": complaint["studentId"]}, include={"user": True})
        if student and student.user:
            await NotificationService(db).create_for_user(
                user_id=student.user.id,
                title="Complaint updated",
                message=f"Your complaint '{complaint['title']}' is now {complaint['status'].lower().replace('_', ' ')}.",
                type_value="COMPLAINT_UPDATE",
                data={"link": "/student/complaints", "complaintId": complaint["id"]},
            )
        return {"message": "Complaint updated successfully", "complaint": complaint}
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error updating complaint")

