from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Promotion
from app.schemas.promotion_schema import (
    PromotionCreate,
    PromotionResponse,
    PromotionUpdate,
)

router = APIRouter(prefix="/promotions", tags=["Promotions"])


@router.get("/", response_model=List[PromotionResponse], status_code=status.HTTP_200_OK)
def get_promotions(session: Session = Depends(get_session)):
    """Récupère toutes les promotions."""
    return session.exec(select(Promotion).order_by(Promotion.id)).all()


@router.get(
    "/{promo_id}", response_model=PromotionResponse, status_code=status.HTTP_200_OK
)
def get_promotion_by_id(promo_id: int, session: Session = Depends(get_session)):
    """Récupère une promotion spécifique par son ID."""
    promo = session.get(Promotion, promo_id)
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Promotion introuvable."
        )
    return promo


@router.post("/", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED)
def create_promotion(
    promo_in: PromotionCreate, session: Session = Depends(get_session)
):
    """Crée une nouvelle promotion."""
    existing = session.exec(
        select(Promotion).where(Promotion.name == promo_in.name)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette promotion existe déjà.",
        )

    new_promo = Promotion(**promo_in.model_dump())
    session.add(new_promo)
    session.commit()
    session.refresh(new_promo)
    return new_promo


@router.patch(
    "/{promo_id}", response_model=PromotionResponse, status_code=status.HTTP_200_OK
)
def update_promotion(
    promo_id: int, promo_in: PromotionUpdate, session: Session = Depends(get_session)
):
    """Met à jour une promotion existante."""
    promo = session.get(Promotion, promo_id)
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Promotion introuvable."
        )

    update_data = promo_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(promo, key, value)

    session.add(promo)
    session.commit()
    session.refresh(promo)
    return promo


@router.delete("/{promo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_promotion(promo_id: int, session: Session = Depends(get_session)):
    """Supprime une promotion."""
    promo = session.get(Promotion, promo_id)
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Promotion introuvable."
        )

    session.delete(promo)
    session.commit()
    return
