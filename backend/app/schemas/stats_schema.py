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

# Dashboard É.M.I.L.E.
class EmileStatsResponse(BaseModel):
    total_students: int
    total_submissions: int
    global_average: float
    group_distribution: Dict[str, int]
    group_averages: Dict[str, float]
    promo_averages: Dict[str, float]
    comparison_tool: Dict[str, float]
    comparison_human_robot: Dict[str, float]
    comparison_motivation: Dict[str, float]