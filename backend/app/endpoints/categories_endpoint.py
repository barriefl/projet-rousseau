from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models import Category
from app.schemas.category_schema import CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=List[CategoryResponse], status_code=status.HTTP_200_OK)
def get_categories(session: Session = Depends(get_session)):
    """Récupère la liste de toutes les catégories existantes."""
    categories = session.exec(select(Category)).all()
    return categories

@router.get("/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
def get_category_by_id(category_id: int, session: Session = Depends(get_session)):
    """Récupère une catégorie spécifique."""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie introuvable."
        )
    return category

@router.patch("/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
def update_category(category_id: int, category_in: CategoryUpdate, session: Session = Depends(get_session)):
    """Met à jour une catégorie existante (ex: changer le type Rousseau ou la pénalité)."""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie introuvable."
        )
        
    update_data = category_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(category, key, value)
        
    session.add(category)
    session.commit()
    session.refresh(category)
    
    return category