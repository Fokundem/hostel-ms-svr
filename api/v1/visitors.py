from fastapi import APIRouter, Depends, HTTPException, status, Query
from prisma import Prisma
from typing import Optional

from database import get_db
from utils.dependencies import get_current_admin, get_current_student
from services.visitor import VisitorService
from schemas.visitors import VisitorRequestCreate, VisitorAdminDecision
from services.notification import NotificationService


router = APIRouter(prefix="/visitors", tags=["Visitors"])


@router.get("", response_model=list[dict])
async def list_visitors(
    status: Optional[str] = Query(None),
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    service = VisitorService(db)
    return await service.list_visitors(status=status)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_visitor_request(
    payload: VisitorRequestCreate,
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_student),
):
    """Student requests a visitor approval."""
    try:
        student = await db.student.find_unique(where={"userId": current_user.id})
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        service = VisitorService(db)
        visitor = await service.request_visit(student.id, payload.model_dump())
        # Notify admins
        await NotificationService(db).create_for_roles(
            roles=["ADMIN", "HOSTEL_MANAGER"],
            title="New visitor request",
            message=f"{current_user.name} submitted a visitor request for {visitor['name']}.",
            type_value="SYSTEM",
            data={"link": "/admin/visitors", "visitorId": visitor["id"]},
        )
        return {"message": "Visitor request submitted", "visitor": visitor}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error submitting visitor request")


@router.get("/student/mine", response_model=list[dict])
async def list_my_visitor_requests(
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_student),
):
    student = await db.student.find_unique(where={"userId": current_user.id})
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    service = VisitorService(db)
    return await service.list_for_student(student.id)


@router.put("/{visitor_id}/decide", response_model=dict)
async def decide_visitor(
    visitor_id: str,
    payload: VisitorAdminDecision,
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    try:
        service = VisitorService(db)
        visitor = await service.admin_decide(
            visitor_id,
            payload.status,
            approved_by=current_user.id,
            rejection_reason=payload.rejectionReason,
        )
        # Notify student
        student = await db.student.find_unique(where={"id": visitor["studentId"]}, include={"user": True})
        if student and student.user:
            await NotificationService(db).create_for_user(
                user_id=student.user.id,
                title="Visitor request updated",
                message=f"Your visitor request for {visitor['name']} was {visitor['status'].lower()}.",
                type_value="SYSTEM",
                data={"link": "/student/visitors", "visitorId": visitor["id"]},
            )
        return {"message": "Visitor request updated", "visitor": visitor}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error updating visitor request")

