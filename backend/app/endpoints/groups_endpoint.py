from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Group
from app.schemas.group_schema import GroupCreate, GroupResponse, GroupUpdate

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("/", response_model=List[GroupResponse], status_code=status.HTTP_200_OK)
def get_groups(session: Session = Depends(get_session)):
    """Récupère tous les groupes."""
    return session.exec(select(Group)).all()


@router.get("/{group_id}", response_model=GroupResponse, status_code=status.HTTP_200_OK)
def get_group_by_id(group_id: int, session: Session = Depends(get_session)):
    """Récupère un groupe spécifique par son ID."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable."
        )
    return group


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(group_in: GroupCreate, session: Session = Depends(get_session)):
    """Crée un nouveau groupe."""
    existing = session.exec(select(Group).where(Group.name == group_in.name)).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce groupe existe déjà pour cet outil.",
        )

    new_group = Group(**group_in.model_dump())
    session.add(new_group)
    session.commit()
    session.refresh(new_group)
    return new_group


@router.patch(
    "/{group_id}", response_model=GroupResponse, status_code=status.HTTP_200_OK
)
def update_group(
    group_id: int, group_in: GroupUpdate, session: Session = Depends(get_session)
):
    """Met à jour un groupe existant."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable."
        )

    update_data = group_in.model_dump(exclude_unset=True)

    if "name" in update_data:
        new_name = update_data["name"]
        duplicate = session.exec(
            select(Group).where(Group.name == new_name, Group.id != group_id)
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un groupe avec ce nom existe déjà.",
            )

    for key, value in update_data.items():
        setattr(group, key, value)

    session.add(group)
    session.commit()
    session.refresh(group)
    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, session: Session = Depends(get_session)):
    """Supprime un groupe."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable."
        )

    session.delete(group)
    session.commit()
    return
