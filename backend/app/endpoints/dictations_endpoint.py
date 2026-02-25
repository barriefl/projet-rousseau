from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import Dictation
from app.schemas.dictation_schema import DictationCreate, DictationResponse
from app.services.correction_service import CorrectionService

router = APIRouter()

@router.post("/", response_model=DictationResponse, status_code=status.HTTP_201_CREATED)
def create_dictation(dictation_in: DictationCreate, session: Session = Depends(get_session)):
    """Crée une nouvelle dictée de référence (saisie manuelle ou issue d'un fichier lu par le front)."""
    
    if not dictation_in.content_reference.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le texte de la dictée ne peut pas être vide."
        )

    new_dictation = Dictation(
        title=dictation_in.title,
        content_reference=dictation_in.content_reference
    )
    
    session.add(new_dictation)
    session.commit()
    session.refresh(new_dictation)
    
    return new_dictation

@router.get("/", response_model=List[DictationResponse], status_code=status.HTTP_200_OK)
def get_dictations(session: Session = Depends(get_session)):
    """Récupère la liste de toutes les dictées de référence."""
    
    dictations_db = session.exec(select(Dictation)).all()
    
    return dictations_db

@router.get("/{dictation_id}", response_model=DictationResponse, status_code=status.HTTP_200_OK)
def get_dictation_by_id(dictation_id: int, session: Session = Depends(get_session)):
    """Récupère une dictée de référence spécifique grâce à son ID."""
    
    dictation = session.get(Dictation, dictation_id)
    
    if not dictation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dictée introuvable."
        )
        
    return dictation

@router.post("/recalculate", status_code=status.HTTP_200_OK)
def recalculate_all_dictations(session: Session = Depends(get_session)):
    """Recalcule les scores de TOUTES les dictées en fonction des catégories actuelles."""
    correction_service = CorrectionService(session)
    dictations = session.exec(select(Dictation)).all()
    
    for dictation in dictations:
        correction_service.recalculate_dictation_scores(dictation)
        
    return {"detail": "Toutes les copies ont été recalculées."}