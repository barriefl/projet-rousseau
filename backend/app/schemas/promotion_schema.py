from typing import Optional

from pydantic import BaseModel


class PromotionBase(BaseModel):
    name: str


class PromotionCreate(PromotionBase):
    pass


class PromotionUpdate(BaseModel):
    name: Optional[str] = None


class PromotionResponse(PromotionBase):
    id: int

    class Config:
        from_attributes = True
