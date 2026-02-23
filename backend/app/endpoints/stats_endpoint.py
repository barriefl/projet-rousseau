from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.stats_service import StatsService
from app.database import get_session
from app.schemas.stats_schema import EmileStatsResponse, GlobalStatsResponse, GroupStatsResponse
import logging

router = APIRouter()

logger = logging.getLogger("uvicorn.error")

def get_stats_service(db: Session = Depends(get_session)) -> StatsService:
    return StatsService(db)

@router.get("/global", response_model=GlobalStatsResponse)
def read_global_stats(service: StatsService = Depends(get_stats_service)):
    """
    Récupère les statistiques globales pour le Dashboard.
    """
    try:
        return service.get_global_kpis()
    except Exception as e:
        logger.error(f"CRASH STATS: {e}")
        raise HTTPException(status_code=500, detail="Impossible de récupérer les statistiques.")
    
@router.get("/groups", response_model=GroupStatsResponse)
def read_group_stats(service: StatsService = Depends(get_stats_service)):
    return service.get_group_stats()

@router.get("/emile", response_model=EmileStatsResponse)
def get_emile_stats(service: StatsService = Depends(get_stats_service)):
    """Récupère les statistiques globales pour le tableau de bord ÉMILE."""
    try:
        return service.get_emile_dashboard_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Impossible de récupérer les statistiques ÉMILE.")