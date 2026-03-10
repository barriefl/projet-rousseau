from typing import Optional

from pydantic import BaseModel, ConfigDict


class PromotionBase(BaseModel):
    name: str


class PromotionCreate(PromotionBase):
    pass


class PromotionUpdate(BaseModel):
    name: Optional[str] = None


class PromotionResponse(PromotionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
