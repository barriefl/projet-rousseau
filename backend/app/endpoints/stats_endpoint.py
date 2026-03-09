from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_session
from app.schemas.stats_schema import EmileStatsResponse, RousseauStatsResponse
from app.services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["Stats"])


def get_stats_service(db: Session = Depends(get_session)) -> StatsService:
    return StatsService(db)


@router.get(
    "/rousseau", response_model=RousseauStatsResponse, status_code=status.HTTP_200_OK
)
def get_rousseau_stats(service: StatsService = Depends(get_stats_service)):
    """Récupère les statistiques spécifiques aux hypothèses de l'Étude Rousseau."""
    try:
        return service.get_rousseau_dashboard_stats()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de récupérer les statistiques de l'étude Rousseau.",
        )


@router.get("/emile", response_model=EmileStatsResponse, status_code=status.HTTP_200_OK)
def get_emile_stats(service: StatsService = Depends(get_stats_service)):
    """Récupère les statistiques globales pour le tableau de bord ÉMILE."""
    try:
        return service.get_emile_dashboard_stats()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de récupérer les statistiques d'ÉMILE.",
        )
