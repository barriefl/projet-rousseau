from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.stats_service import StatsService
from app.database import init_db
from backend.app.schemas.stats_schema import GlobalStatsResponse

router = APIRouter()

def get_stats_service(db: Session = Depends(init_db)) -> StatsService:
    return StatsService(db)

@router.get("/global", response_model=GlobalStatsResponse)
def read_global_stats(service: StatsService = Depends(get_stats_service)):
    """
    Récupère les statistiques globales pour le Dashboard.
    """
    try:
        return service.get_global_kpis()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Impossible de récupérer les statistiques.")