from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import Tool
from app.schemas.tool_schema import ToolCreate, ToolRead, ToolUpdate

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("/", response_model=List[ToolRead], status_code=status.HTTP_200_OK)
def get_tools(session: Session = Depends(get_session)):
    """Récupère la liste de tous les outils disponibles."""
    return session.exec(select(Tool)).all()


@router.get("/{tool_id}", response_model=ToolRead, status_code=status.HTTP_200_OK)
def get_tool(tool_id: int, session: Session = Depends(get_session)):
    """Récupère un outil spécifique par son ID."""
    tool = session.get(Tool, tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Outil non trouvé."
        )
    return tool


@router.post("/", response_model=ToolRead, status_code=status.HTTP_201_CREATED)
def create_tool(tool_in: ToolCreate, session: Session = Depends(get_session)):
    """Crée un nouvel outil (ex: PV, E+)."""
    existing = session.exec(select(Tool).where(Tool.name == tool_in.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cet outil existe déjà."
        )

    db_tool = Tool.model_validate(tool_in)
    session.add(db_tool)
    session.commit()
    session.refresh(db_tool)
    return db_tool


@router.patch("/{tool_id}", response_model=ToolRead)
def update_tool(
    tool_id: int, tool_in: ToolUpdate, session: Session = Depends(get_session)
):
    """Met à jour partiellement un outil."""
    db_tool = session.get(Tool, tool_id)
    if not db_tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Outil non trouvé."
        )

    update_data = tool_in.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_tool, key, value)

    session.add(db_tool)
    session.commit()
    session.refresh(db_tool)
    return db_tool


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tool(tool_id: int, session: Session = Depends(get_session)):
    """Supprime un outil."""
    tool = session.get(Tool, tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Outil non trouvé."
        )

    session.delete(tool)
    session.commit()
    return None
