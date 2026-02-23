from pydantic import BaseModel
import uuid
from typing import Optional

from app.models import Group

class StudentResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    promo: Optional[str] = None
    group: Optional[str] = None

class StudentProgressionResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    group: Optional[str] = None
    score_initial: Optional[float] = None
    score_final: Optional[float] = None
    progress: Optional[float] = None

class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    promo: Optional[str] = None
    group: Optional[Group] = None