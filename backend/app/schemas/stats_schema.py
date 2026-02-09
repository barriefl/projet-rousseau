from pydantic import BaseModel

class VoltaireStats(BaseModel):
    avg_init: float
    avg_final: float
    progression: float

class EcriPlusStats(BaseModel):
    avg_init: float
    avg_final: float
    progression: float

class GlobalStatsResponse(BaseModel):
    total_students: int
    voltaire: VoltaireStats
    ecriplus: EcriPlusStats