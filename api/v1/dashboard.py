from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from services.dashboard import DashboardService
from utils.dependencies import get_current_admin

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=dict)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get statistics for the admin dashboard"""
    try:
        service = DashboardService(db)
        stats = service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
