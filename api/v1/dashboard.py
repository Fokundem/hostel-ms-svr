from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.services.dashboard import DashboardService
from app.utils.dependencies import get_current_admin
from prisma import Prisma

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=dict)
async def get_dashboard_stats(
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get statistics for the admin dashboard"""
    try:
        service = DashboardService(db)
        stats = await service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
