from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models import GradingScale
from app.schemas.grading_scale_schema import GradingScaleCreate, GradingScaleResponse, GradingScaleWithRules

router = APIRouter()

@router.get("/", response_model=List[GradingScaleWithRules], status_code=status.HTTP_200_OK)
def get_all_grading_scales(session: Session = Depends(get_session)):
    """Récupère la liste de toutes les typologies de fautes (le barème)."""
    scales = session.exec(select(GradingScale)).all()

    result = []
    for scale in scales:
        result.append({
            "id": scale.id,
            "name": scale.name,
            "description": scale.description,
            "type_rousseau": scale.type_rousseau.value if hasattr(scale.type_rousseau, 'value') else scale.type_rousseau,
            "penalty": scale.penalty,
            "rules": scale.rules
        })
        
    return result

@router.post("/", response_model=GradingScaleResponse, status_code=status.HTTP_201_CREATED)
def create_grading_scale(scale_in: GradingScaleCreate, session: Session = Depends(get_session)):
    """Crée une nouvelle typologie dans le barème."""
    
    existing = session.exec(select(GradingScale).where(GradingScale.name == scale_in.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Le nom de typologie '{scale_in.name}' existe déjà."
        )
        
    new_scale = GradingScale(
        name=scale_in.name,
        description=scale_in.description,
        type_rousseau=scale_in.type_rousseau,
        penalty=scale_in.penalty
    )
    
    session.add(new_scale)
    session.commit()
    session.refresh(new_scale)
    
    return new_scale

@router.delete("/{scale_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grading_scale(scale_id: int, session: Session = Depends(get_session)):
    """Supprime une typologie grâce à son ID."""
    
    scale = session.get(GradingScale, scale_id)
    if not scale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Typologie introuvable."
        )
        
    session.delete(scale)
    session.commit()
    return