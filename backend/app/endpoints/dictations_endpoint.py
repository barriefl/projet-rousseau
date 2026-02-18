from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_session
from app.models import Dictation
from app.schemas.dictation_schema import DictationCreate, DictationResponse

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