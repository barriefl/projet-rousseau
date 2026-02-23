from typing import Dict, Optional
from pydantic import BaseModel

# Dashboard Étude Rousseau.
class RousseauStatsResponse(BaseModel):
    tools_vs_dictation: Dict[str, Dict[str, float]]
    equivalence_g2_g5: Dict[str, float]
    teacher_factor: Dict[str, float]
    sociocultural_impact: Dict[str, Dict[str, float]]

# Dashboard É.M.I.L.E.
class EmileStatsResponse(BaseModel):
    total_students: int
    total_submissions: int
    global_average: float
    group_distribution: Dict[str, int]
    group_averages: Dict[str, Dict[str, float]]
    promo_averages: Dict[str, Dict[str, float]]
    comparison_tool: Dict[str, Dict[str, float]]
    comparison_human_robot: Dict[str, Dict[str, float]]
    comparison_motivation: Dict[str, Dict[str, float]]