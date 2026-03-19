from fastapi import APIRouter, Depends, HTTPException, Query
from prisma import Prisma

from database import get_db
from utils.dependencies import get_current_user
from services.notification import NotificationService


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/mine", response_model=list[dict])
async def list_my_notifications(
    unread_only: bool = Query(False),
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NotificationService(db)
    return await service.list_for_user(current_user.id, unread_only=unread_only)


@router.put("/{notification_id}/read", response_model=dict)
async def mark_notification_read(
    notification_id: str,
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        service = NotificationService(db)
        return await service.mark_read(notification_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/mine/read-all", response_model=dict)
async def mark_all_read(
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = NotificationService(db)
    return await service.mark_all_read(current_user.id)


@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(
    notification_id: str,
    db: Prisma = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        service = NotificationService(db)
        return await service.delete(notification_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

