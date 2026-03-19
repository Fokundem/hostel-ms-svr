from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from utils.dependencies import get_current_admin, get_current_user
from services.hostel import HostelService
from schemas.hostels import HostelCreate, HostelResponse


router = APIRouter(prefix="/hostels", tags=["Hostels"])


@router.get("", response_model=list[HostelResponse])
def list_hostels(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = HostelService(db)
    return service.list_hostels()


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_hostel(
    payload: HostelCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    try:
        service = HostelService(db)
        hostel = service.create_hostel(payload.model_dump())
        return {"message": "Hostel created successfully", "hostel": hostel}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
