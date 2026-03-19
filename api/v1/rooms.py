from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from services.room import RoomService
from schemas.room import RoomResponse, RoomDetailResponse, RoomCreate, RoomUpdate
from utils.dependencies import get_current_user, get_current_admin
from models import Hostel
from typing import Optional, List

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("", response_model=List[RoomResponse])
def get_available_rooms(
    hostel_id: Optional[str] = Query(None),
    floor: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all available rooms (students & admins can view)"""
    try:
        service = RoomService(db)
        rooms = service.get_available_rooms(hostel_id=hostel_id, floor=floor)
        return rooms
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/all", response_model=List[RoomResponse])
def get_all_rooms(
    hostel_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get all rooms including full and maintenance (admin only)"""
    try:
        service = RoomService(db)
        rooms = service.get_all_rooms(hostel_id=hostel_id)
        return rooms
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{room_id}", response_model=RoomDetailResponse)
def get_room_details(
    room_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get room details by ID"""
    try:
        service = RoomService(db)
        room = service.get_room_by_id(room_id)
        return room
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_room(
    room_data: RoomCreate,
    hostel_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create a new room (admin only)"""
    try:
        if not hostel_id:
            hostel = db.execute(select(Hostel).limit(1)).scalar_one_or_none()
            if not hostel:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No hostel found. Create a hostel first.",
                )
            hostel_id = hostel.id
        service = RoomService(db)
        room = service.create_room(hostel_id, room_data)
        return {"message": "Room created successfully", "room": room}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{room_id}", response_model=RoomDetailResponse)
def update_room(
    room_id: str,
    room_data: RoomUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Update room details (admin only)"""
    try:
        service = RoomService(db)
        room = service.update_room(room_id, room_data)
        return room
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{room_id}", response_model=dict)
def delete_room(
    room_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Delete a room (admin only)"""
    try:
        service = RoomService(db)
        result = service.delete_room(room_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
