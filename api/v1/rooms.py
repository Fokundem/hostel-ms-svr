from fastapi import APIRouter, Depends, HTTPException, status, Query
from database import get_db
from services.room import RoomService
from schemas.room import RoomResponse, RoomDetailResponse, RoomCreate, RoomUpdate
from utils.dependencies import get_current_user, get_current_admin
from prisma import Prisma
from typing import Optional, List

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("", response_model=List[RoomResponse])
async def get_available_rooms(
    hostel_id: Optional[str] = Query(None),
    floor: Optional[str] = Query(None),
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all available rooms (students & admins can view)"""
    try:
        service = RoomService(db)
        rooms = await service.get_available_rooms(hostel_id=hostel_id, floor=floor)
        return rooms
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/all", response_model=List[RoomResponse])
async def get_all_rooms(
    hostel_id: Optional[str] = Query(None),
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get all rooms including full and maintenance (admin only)"""
    try:
        service = RoomService(db)
        rooms = await service.get_all_rooms(hostel_id=hostel_id)
        return rooms
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{room_id}", response_model=RoomDetailResponse)
async def get_room_details(
    room_id: str,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get room details by ID"""
    try:
        service = RoomService(db)
        room = await service.get_room_by_id(room_id)
        return room
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    hostel_id: Optional[str] = Query(None),
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create a new room (admin only)"""
    try:
        if not hostel_id:
            hostel = await db.hostel.find_first()
            if not hostel:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No hostel found. Create a hostel first.",
                )
            hostel_id = hostel.id
        service = RoomService(db)
        room = await service.create_room(hostel_id, room_data)
        return {"message": "Room created successfully", "room": room}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{room_id}", response_model=RoomDetailResponse)
async def update_room(
    room_id: str,
    room_data: RoomUpdate,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Update room details (admin only)"""
    try:
        service = RoomService(db)
        room = await service.update_room(room_id, room_data)
        return room
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{room_id}", response_model=dict)
async def delete_room(
    room_id: str,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Delete a room (admin only)"""
    try:
        service = RoomService(db)
        result = await service.delete_room(room_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
