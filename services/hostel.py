from sqlalchemy.orm import Session
from sqlalchemy import select, asc
from typing import List

from models import Hostel


class HostelService:
    def __init__(self, db: Session):
        self.db = db

    def list_hostels(self) -> List[dict]:
        hostels = self.db.execute(
            select(Hostel).order_by(asc(Hostel.createdAt))
        ).scalars().all()
        return [
            {
                "id": h.id,
                "name": h.name,
                "code": h.code,
                "totalRooms": h.totalRooms,
                "createdAt": h.createdAt,
                "updatedAt": h.updatedAt,
            }
            for h in hostels
        ]

    def create_hostel(self, data: dict) -> dict:
        hostel = Hostel(
            name=data["name"],
            code=data["code"],
            totalRooms=data["totalRooms"],
        )
        self.db.add(hostel)
        self.db.commit()
        self.db.refresh(hostel)
        return {
            "id": hostel.id,
            "name": hostel.name,
            "code": hostel.code,
            "totalRooms": hostel.totalRooms,
            "createdAt": hostel.createdAt,
            "updatedAt": hostel.updatedAt,
        }
