from typing import Dict, Optional
from pydantic import BaseModel

# get_global_kpis

class SubmissionsStats(BaseModel):
    total: int
    avg_init: float
    avg_final: float
    progression: float

class VoltaireStats(BaseModel):
    total: int
    avg_init: float
    avg_final: float
    progression: float

class EcriPlusStats(BaseModel):
    total: int
    avg_init: float
    avg_final: float
    progression: float

class GlobalStatsResponse(BaseModel):
    total_students: int
    submissions: SubmissionsStats
    voltaire: VoltaireStats
    ecriplus: EcriPlusStats

# get_group_stats

class StatsBase(BaseModel):
    total: int
    avg_init: float
    avg_final: float
    progression: float

class SubmissionsStats(StatsBase):
    pass

class ExternalStats(StatsBase):
    platform_name: str

class GroupStatsDetail(BaseModel):
    student_count: int
    dictations: SubmissionsStats
    external_assessment: Optional[ExternalStats] = None

class GroupStatsResponse(BaseModel):
    total_groups: int
    groups: Dict[str, GroupStatsDetail]