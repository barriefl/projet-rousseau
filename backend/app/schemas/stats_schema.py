from typing import Any, Dict

from pydantic import BaseModel


# Dashboard Étude Rousseau.
class TeacherStat(BaseModel):
    score: float
    effectif: int


class RousseauStatsResponse(BaseModel):
    h1_summary: Dict[str, Any]
    h2_equivalence: Dict[str, Any]
    h2_boxplots: Dict[str, Any]
    h2_stats_test: Dict[str, Any]
    h3_teacher: Dict[str, TeacherStat]
    h4_sociocultural: Dict[str, Any]
    regression_model: Dict[str, Any]

    class Config:
        from_attributes = True


# Dashboard É.M.I.L.E.
class EmileStatsResponse(BaseModel):
    total_students: int
    total_submissions: int
    global_average: float
    group_distribution_by_promo: Dict[str, Dict[str, int]]
    group_averages: Dict[str, Dict[str, float]]
    promo_averages: Dict[str, Dict[str, float]]
    comparison_tool: Dict[str, Dict[str, float]]
    comparison_human_robot: Dict[str, Dict[str, float]]
    comparison_motivation: Dict[str, float]
    mistakes_stats: Dict[str, Any]
