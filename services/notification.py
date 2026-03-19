from prisma import Prisma, Json
from typing import Optional, Any, Iterable


class NotificationService:
    def __init__(self, db: Prisma):
        self.db = db

    async def list_for_user(self, user_id: str, unread_only: bool = False) -> list[dict]:
        where = {"userId": user_id}
        if unread_only:
            where["read"] = False
        rows = await self.db.notification.find_many(where=where, order={"createdAt": "desc"})
        return [
            {
                "id": n.id,
                "userId": n.userId,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "read": n.read,
                "data": n.data,
                "createdAt": n.createdAt,
            }
            for n in rows
        ]

    async def mark_read(self, notification_id: str, user_id: str) -> dict:
        n = await self.db.notification.find_unique(where={"id": notification_id})
        if not n or n.userId != user_id:
            raise ValueError("Notification not found")
        n = await self.db.notification.update(where={"id": notification_id}, data={"read": True})
        return {"id": n.id, "read": n.read}

    async def mark_all_read(self, user_id: str) -> dict:
        await self.db.notification.update_many(where={"userId": user_id, "read": False}, data={"read": True})
        return {"ok": True}

    async def delete(self, notification_id: str, user_id: str) -> dict:
        n = await self.db.notification.find_unique(where={"id": notification_id})
        if not n or n.userId != user_id:
            raise ValueError("Notification not found")
        await self.db.notification.delete(where={"id": notification_id})
        return {"ok": True}

    async def create_for_user(
        self,
        user_id: str,
        title: str,
        message: str,
        type_value: str = "SYSTEM",
        data: Optional[Any] = None,
    ) -> None:
        json_data = Json(data) if data is not None else None
        await self.db.notification.create(
            data={
                "userId": user_id,
                "title": title,
                "message": message,
                "type": type_value,
                "data": json_data,
            }
        )

    async def create_for_roles(
        self,
        roles: Iterable[str],
        title: str,
        message: str,
        type_value: str = "SYSTEM",
        data: Optional[Any] = None,
    ) -> None:
        users = await self.db.user.find_many(where={"role": {"in": list(roles)}})
        for u in users:
            await self.create_for_user(u.id, title, message, type_value=type_value, data=data)

