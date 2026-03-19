from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List

from utils.exceptions import RoomNotFoundException
from models import Room, RoomStatusEnum
from schemas.room import RoomCreate, RoomUpdate


def _room_to_dict(room: Room) -> dict:
    status_val = room.status.value if hasattr(room.status, "value") else str(room.status)
    return {
        "id": room.id,
        "roomNumber": room.roomNumber,
        "floor": room.floor,
        "block": room.block,
        "capacity": room.capacity,
        "occupied": room.occupied,
        "status": status_val,
        "amenities": room.amenities or [],
        "price": room.price,
        "hostelId": room.hostelId,
        "createdAt": room.createdAt.isoformat() if room.createdAt else None,
    }


class RoomService:
    def __init__(self, db: Session):
        self.db = db

    def get_available_rooms(self, hostel_id: Optional[str] = None, floor: Optional[str] = None) -> List[dict]:
        q = select(Room).where(Room.status == RoomStatusEnum.AVAILABLE)
        if hostel_id:
            q = q.where(Room.hostelId == hostel_id)
        if floor:
            q = q.where(Room.floor == floor)
        rooms = self.db.execute(q).scalars().all()
        return [_room_to_dict(r) for r in rooms]

    def get_all_rooms(self, hostel_id: Optional[str] = None) -> List[dict]:
        q = select(Room)
        if hostel_id:
            q = q.where(Room.hostelId == hostel_id)
        rooms = self.db.execute(q).scalars().all()
        return [_room_to_dict(r) for r in rooms]

    def get_room_by_id(self, room_id: str) -> dict:
        room = self.db.execute(select(Room).where(Room.id == room_id)).scalar_one_or_none()
        if not room:
            raise RoomNotFoundException()
        return _room_to_dict(room)

    def create_room(self, hostel_id: str, room_data: RoomCreate) -> dict:
        room = Room(
            roomNumber=room_data.roomNumber,
            floor=room_data.floor,
            block=room_data.block,
            hostelId=hostel_id,
            capacity=room_data.capacity,
            amenities=room_data.amenities or [],
            price=room_data.price,
            status=RoomStatusEnum.AVAILABLE,
            occupied=0,
        )
        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)
        return _room_to_dict(room)

    def update_room(self, room_id: str, room_data: RoomUpdate) -> dict:
        room = self.db.execute(select(Room).where(Room.id == room_id)).scalar_one_or_none()
        if not room:
            raise RoomNotFoundException()
        data = room_data.model_dump(exclude_unset=True)
        if "status" in data and isinstance(data["status"], str):
            data["status"] = RoomStatusEnum(data["status"])
        for k, v in data.items():
            setattr(room, k, v)
        self.db.commit()
        self.db.refresh(room)
        return _room_to_dict(room)

    def delete_room(self, room_id: str) -> dict:
        room = self.db.execute(select(Room).where(Room.id == room_id)).scalar_one_or_none()
        if not room:
            raise RoomNotFoundException()
        self.db.delete(room)
        self.db.commit()
        return {"message": "Room deleted successfully"}
