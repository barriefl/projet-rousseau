from pydantic import BaseModel

class SubmissionsStats(BaseModel):
    avg_init: float
    avg_final: float
    progression: float

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
    submissions: SubmissionsStats
    voltaire: VoltaireStats
    ecriplus: EcriPlusStats