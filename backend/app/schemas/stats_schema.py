from pydantic import BaseModel

class VoltaireStats(BaseModel):
    average_initial: float
    average_final: float
    progression: float

class EcriPlusStats(BaseModel):
    average_initial: float
    average_final: float
    progression: float

class GlobalStatsResponse(BaseModel):
    total_students: int
    voltaire: VoltaireStats
    ecri_plus: EcriPlusStats