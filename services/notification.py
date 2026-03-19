from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import Optional, Any, Iterable

from models import Notification, User, NotificationTypeEnum, RoleEnum


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user_id: str, unread_only: bool = False) -> list[dict]:
        q = select(Notification).where(Notification.userId == user_id).order_by(desc(Notification.createdAt))
        if unread_only:
            q = q.where(Notification.read == False)
        notifications = self.db.execute(q).scalars().all()
        return [
            {
                "id": n.id,
                "userId": n.userId,
                "title": n.title,
                "message": n.message,
                "type": n.type.value if hasattr(n.type, "value") else str(n.type),
                "read": n.read,
                "data": n.data,
                "createdAt": n.createdAt.isoformat() if n.createdAt else None,
            }
            for n in notifications
        ]

    def mark_read(self, notification_id: str, user_id: str) -> dict:
        n = self.db.execute(
            select(Notification).where(Notification.id == notification_id, Notification.userId == user_id)
        ).scalar_one_or_none()
        if not n:
            raise ValueError("Notification not found")
        n.read = True
        self.db.commit()
        self.db.refresh(n)
        return {"id": n.id, "read": n.read}

    def mark_all_read(self, user_id: str) -> dict:
        notifications = self.db.execute(
            select(Notification).where(Notification.userId == user_id, Notification.read == False)
        ).scalars().all()
        for n in notifications:
            n.read = True
        self.db.commit()
        return {"ok": True}

    def delete(self, notification_id: str, user_id: str) -> dict:
        n = self.db.execute(
            select(Notification).where(Notification.id == notification_id, Notification.userId == user_id)
        ).scalar_one_or_none()
        if not n:
            raise ValueError("Notification not found")
        self.db.delete(n)
        self.db.commit()
        return {"ok": True}

    def create_for_user(
        self,
        user_id: str,
        title: str,
        message: str,
        type_value: str = "SYSTEM",
        data: Optional[Any] = None,
    ) -> None:
        type_enum = NotificationTypeEnum(type_value) if type_value in [e.value for e in NotificationTypeEnum] else NotificationTypeEnum.SYSTEM
        n = Notification(
            userId=user_id,
            title=title,
            message=message,
            type=type_enum,
            data=data,
        )
        self.db.add(n)
        self.db.commit()

    def create_for_roles(
        self,
        roles: Iterable[str],
        title: str,
        message: str,
        type_value: str = "SYSTEM",
        data: Optional[Any] = None,
    ) -> None:
        role_enums = [RoleEnum(r) for r in roles if r in [e.value for e in RoleEnum]]
        users = self.db.execute(select(User).where(User.role.in_(role_enums))).scalars().all()
        for u in users:
            self.create_for_user(u.id, title, message, type_value=type_value, data=data)
