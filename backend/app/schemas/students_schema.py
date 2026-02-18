from pydantic import BaseModel
import uuid
from typing import Optional

class StudentResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    promo: str
    group: str