from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models import Category, Rule
from app.schemas.rule_schema import RuleCreate, RuleUpdate, RuleResponse

router = APIRouter()

@router.get("/", response_model=List[RuleResponse])
def get_all_rules(session: Session = Depends(get_session)):
    """Récupère toutes les règles LanguageTool enregistrées."""
    return session.exec(select(Rule)).all()

@router.get("/unclassified", response_model=List[RuleResponse])
def get_unclassified_rules(session: Session = Depends(get_session)):
    """Récupère uniquement les règles qui n'ont pas encore été assignées à une catégorie."""
    return session.exec(select(Rule).where(Rule.category_id == None)).all()

@router.post("/", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(rule_in: RuleCreate, session: Session = Depends(get_session)):
    """Crée manuellement une nouvelle règle."""
    existing = session.exec(select(Rule).where(Rule.lt_rule_id == rule_in.lt_rule_id)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cette règle existe déjà.")
    
    new_rule = Rule(**rule_in.model_dump())
    session.add(new_rule)
    session.commit()
    session.refresh(new_rule)
    return new_rule

@router.patch("/{rule_id}", response_model=RuleResponse)
def update_rule(rule_id: int, rule_in: RuleUpdate, session: Session = Depends(get_session)):
    """Met à jour une règle (ex: la classer dans une catégorie ou la désactiver)."""
    rule = session.get(Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Règle introuvable.")
    
    update_data = rule_in.model_dump(exclude_unset=True)

    if "category_id" in update_data:
        cat_id = update_data["category_id"]
        if cat_id is not None:
            category = session.get(Category, cat_id)
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catégorie introuvable.")
        
        rule.category_id = cat_id

    if "description" in update_data:
        rule.description = update_data["description"]
        
    if "is_active" in update_data:
        rule.is_active = update_data["is_active"]

    session.add(rule)
    session.commit()
    session.refresh(rule)
    
    return rule

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, session: Session = Depends(get_session)):
    """Supprime une règle de la base."""
    rule = session.get(Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Règle introuvable.")
        
    session.delete(rule)
    session.commit()
    return