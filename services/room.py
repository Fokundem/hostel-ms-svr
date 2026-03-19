from prisma import Prisma
from utils.exceptions import RoomNotFoundException, RoomFullException, AllocationNotFoundException
from schemas.room import RoomCreate, RoomUpdate, RoomAllocationCreate
from typing import Optional, List


class RoomService:
    def __init__(self, db: Prisma):
        self.db = db

    async def get_available_rooms(self, hostel_id: Optional[str] = None, floor: Optional[str] = None) -> List[dict]:
        """Get all available rooms, optionally filtered by hostel and floor"""
        filters = {}
        if hostel_id:
            filters["hostelId"] = hostel_id
        if floor:
            filters["floor"] = floor
        
        filters["status"] = "AVAILABLE"
        
        rooms = await self.db.room.find_many(where=filters)
        return [
            {
                "id": room.id,
                "roomNumber": room.roomNumber,
                "floor": room.floor,
                "block": room.block,
                "capacity": room.capacity,
                "occupied": room.occupied,
                "status": room.status,
                "amenities": room.amenities,
                "price": room.price,
                "hostelId": room.hostelId,
                "createdAt": room.createdAt.isoformat(),
            }
            for room in rooms
        ]

    async def get_all_rooms(self, hostel_id: Optional[str] = None) -> List[dict]:
        """Get all rooms (including full and maintenance), optionally filtered by hostel"""
        filters = {}
        if hostel_id:
            filters["hostelId"] = hostel_id
        
        rooms = await self.db.room.find_many(where=filters)
        return [
            {
                "id": room.id,
                "roomNumber": room.roomNumber,
                "floor": room.floor,
                "block": room.block,
                "capacity": room.capacity,
                "occupied": room.occupied,
                "status": room.status,
                "amenities": room.amenities,
                "price": room.price,
                "hostelId": room.hostelId,
                "createdAt": room.createdAt.isoformat(),
            }
            for room in rooms
        ]

    async def get_room_by_id(self, room_id: str) -> dict:
        """Get room details by ID"""
        room = await self.db.room.find_unique(where={"id": room_id})
        if not room:
            raise RoomNotFoundException()
        
        return {
            "id": room.id,
            "roomNumber": room.roomNumber,
            "floor": room.floor,
            "block": room.block,
            "capacity": room.capacity,
            "occupied": room.occupied,
            "status": room.status,
            "amenities": room.amenities,
            "price": room.price,
            "hostelId": room.hostelId,
            "createdAt": room.createdAt.isoformat(),
        }

    async def get_rooms_by_hostel(self, hostel_id: str) -> List[dict]:
        """Get all rooms in a hostel"""
        return await self.get_all_rooms(hostel_id=hostel_id)

    async def create_room(self, hostel_id: str, room_data: RoomCreate) -> dict:
        """Create a new room (admin only)"""
        new_room = await self.db.room.create(
            data={
                "roomNumber": room_data.roomNumber,
                "floor": room_data.floor,
                "block": room_data.block,
                "hostelId": hostel_id,
                "capacity": room_data.capacity,
                "amenities": room_data.amenities,
                "price": room_data.price,
                "status": "AVAILABLE",
                "occupied": 0,
            }
        )
        
        return {
            "id": new_room.id,
            "roomNumber": new_room.roomNumber,
            "floor": new_room.floor,
            "block": new_room.block,
            "capacity": new_room.capacity,
            "occupied": new_room.occupied,
            "status": new_room.status,
            "amenities": new_room.amenities,
            "price": new_room.price,
            "hostelId": new_room.hostelId,
            "createdAt": new_room.createdAt.isoformat(),
        }

    async def update_room(self, room_id: str, room_data: RoomUpdate) -> dict:
        """Update room details (admin only)"""
        room = await self.db.room.find_unique(where={"id": room_id})
        if not room:
            raise RoomNotFoundException()
        
        update_fields = room_data.dict(exclude_unset=True)
        updated_room = await self.db.room.update(
            where={"id": room_id},
            data=update_fields
        )
        
        return {
            "id": updated_room.id,
            "roomNumber": updated_room.roomNumber,
            "floor": updated_room.floor,
            "block": updated_room.block,
            "capacity": updated_room.capacity,
            "occupied": updated_room.occupied,
            "status": updated_room.status,
            "amenities": updated_room.amenities,
            "price": updated_room.price,
            "hostelId": updated_room.hostelId,
            "createdAt": updated_room.createdAt.isoformat(),
        }

    async def delete_room(self, room_id: str) -> dict:
        """Delete a room (admin only)"""
        room = await self.db.room.find_unique(where={"id": room_id})
        if not room:
            raise RoomNotFoundException()
        
        await self.db.room.delete(where={"id": room_id})
        return {"message": "Room deleted successfully"}
