from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from database import get_db
from utils.dependencies import get_current_admin, get_current_student
from services.complaint import ComplaintService
from schemas.complaints import ComplaintCreate, ComplaintAdminUpdate
from services.notification import NotificationService
from models import Student


router = APIRouter(prefix="/complaints", tags=["Complaints"])


def _get_student_by_user_id(db: Session, user_id: str):
    return db.execute(select(Student).where(Student.userId == user_id)).scalar_one_or_none()


@router.get("", response_model=list[dict])
def list_complaints(
    filter_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    service = ComplaintService(db)
    return service.list_all(status=filter_status)


@router.get("/student/mine", response_model=list[dict])
def list_my_complaints(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_student),
):
    student = _get_student_by_user_id(db, current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    service = ComplaintService(db)
    return service.list_for_student(student.id)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_complaint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_student),
):
    try:
        student = _get_student_by_user_id(db, current_user.id)
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        service = ComplaintService(db)
        complaint = service.create_complaint(student.id, payload.model_dump())
        NotificationService(db).create_for_roles(
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
def admin_update_complaint(
    complaint_id: str,
    payload: ComplaintAdminUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    try:
        service = ComplaintService(db)
        complaint = service.admin_update(complaint_id, payload.model_dump(exclude_unset=True))
        student = db.execute(select(Student).where(Student.id == complaint["studentId"])).scalar_one_or_none()
        if student:
            status_str = str(complaint.get("status", "")).lower().replace("_", " ")
            NotificationService(db).create_for_user(
                user_id=student.userId,
                title="Complaint updated",
                message=f"Your complaint '{complaint['title']}' is now {status_str}.",
                type_value="COMPLAINT_UPDATE",
                data={"link": "/student/complaints", "complaintId": complaint["id"]},
            )
        return {"message": "Complaint updated successfully", "complaint": complaint}
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error updating complaint")
