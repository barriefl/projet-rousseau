from app.models import AssessmentResult, AssessmentType, Platform, Student, Submission
from sqlalchemy import func
from sqlalchemy.orm import Session

class StatsService:
    def __init__(self, db: Session):
        self.db = db

    def get_global_kpis(self):
        """Récupère les indicateurs clés globaux."""
        total_students = self.db.query(Student).count()

        # Implémenter la moyenne des scores initiaux et finaux pour les dictées.
        # dictations_avg_init = db.session.query(db.func.avg(Submission.score))\

        def get_avg_score(a_platform, a_type):
            result = self.db.query(func.avg(AssessmentResult.score))\
                .filter(AssessmentResult.platform == a_platform)\
                .filter(AssessmentResult.type == a_type)\
                .scalar()
            return result or 0.0
        
        voltaire_avg_init = get_avg_score(Platform.VOLTAIRE, AssessmentType.INITIAL)
        voltaire_avg_final = get_avg_score(Platform.VOLTAIRE, AssessmentType.FINAL)

        ecriplus_avg_init = get_avg_score(Platform.ECRIPLUS, AssessmentType.INITIAL)
        ecriplus_avg_final = get_avg_score(Platform.ECRIPLUS, AssessmentType.FINAL)
        
        voltaire_progression = voltaire_avg_final - voltaire_avg_init
        ecriplus_progression = ecriplus_avg_final - ecriplus_avg_init

        return {
            "total_students": total_students,
            "voltaire": {
                    "avg_init": round(voltaire_avg_init, 2),
                    "avg_final": round(voltaire_avg_final, 2),
                    "progression": round(voltaire_progression, 2)
            },
            "ecriplus": {
                    "avg_init": round(ecriplus_avg_init, 2),
                    "avg_final": round(ecriplus_avg_final, 2),
                    "progression": round(ecriplus_progression, 2)
            }
        }
