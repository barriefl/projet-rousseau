from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.stats_service import StatsService
from app.database import get_session
from app.schemas.stats_schema import EmileStatsResponse, RousseauStatsResponse

router = APIRouter()

def get_stats_service(db: Session = Depends(get_session)) -> StatsService:
    return StatsService(db)

@router.get("/rousseau", response_model=RousseauStatsResponse)
def get_rousseau_stats(service: StatsService = Depends(get_stats_service)):
    """Récupère les statistiques spécifiques aux hypothèses de l'Étude Rousseau."""
    try:
        return service.get_rousseau_dashboard_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Impossible de récupérer les statistiques de l'étude Rousseau.")

@router.get("/emile", response_model=EmileStatsResponse)
def get_emile_stats(service: StatsService = Depends(get_stats_service)):
    """Récupère les statistiques globales pour le tableau de bord ÉMILE."""
    try:
        return service.get_emile_dashboard_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Impossible de récupérer les statistiques d'ÉMILE.")