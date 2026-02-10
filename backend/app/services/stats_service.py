from app.models import AssessmentResult, AssessmentType, Platform, Student, Submission
from sqlalchemy import Float, cast, func
from sqlalchemy.orm import Session

class StatsService:
    def __init__(self, db: Session):
        self.db = db

    def get_global_kpis(self):
        """Récupère les indicateurs clés globaux."""
        total_students = self.db.query(Student).count()
        total_submissions = self.db.query(Submission).count()
        total_voltaire_assessments = self.db.query(AssessmentResult)\
            .filter(AssessmentResult.platform == Platform.VOLTAIRE)\
            .count()
        total_ecriplus_assessments = self.db.query(AssessmentResult)\
            .filter(AssessmentResult.platform == Platform.ECRIPLUS)\
            .count()

        def get_dictation_avg(a_type):
            result = self.db.query(
                func.avg(
                    cast(
                        func.json_extract_path_text(Submission.scores, 'raw'), 
                        Float
                    )
                )
            )\
            .filter(Submission.assessment_type == a_type)\
            .scalar()
            return result or 0.0

        submissions_avg_init = get_dictation_avg(AssessmentType.INITIAL)
        submissions_avg_final = get_dictation_avg(AssessmentType.FINAL)

        def get_avg_score(a_platform, a_type):
            result = self.db.query(func.avg(AssessmentResult.score))\
                .filter(AssessmentResult.platform == a_platform)\
                .filter(AssessmentResult.assessment_type == a_type)\
                .scalar()
            return result or 0.0
        
        voltaire_avg_init = get_avg_score(Platform.VOLTAIRE, AssessmentType.INITIAL)
        voltaire_avg_final = get_avg_score(Platform.VOLTAIRE, AssessmentType.FINAL)

        ecriplus_avg_init = get_avg_score(Platform.ECRIPLUS, AssessmentType.INITIAL)
        ecriplus_avg_final = get_avg_score(Platform.ECRIPLUS, AssessmentType.FINAL)

        submissions_progression = submissions_avg_final- submissions_avg_init
        voltaire_progression = voltaire_avg_final - voltaire_avg_init
        ecriplus_progression = ecriplus_avg_final - ecriplus_avg_init

        return {
            "total_students": total_students,
            "submissions": {
                "total": total_submissions,
                "avg_init": round(submissions_avg_init, 2),
                "avg_final": round(submissions_avg_final, 2),
                "progression": round(submissions_progression, 2)
            },
            "voltaire": {
                "total": total_voltaire_assessments,
                "avg_init": round(voltaire_avg_init, 2),
                "avg_final": round(voltaire_avg_final, 2),
                "progression": round(voltaire_progression, 2)
            },
            "ecriplus": {
                "total": total_ecriplus_assessments,
                "avg_init": round(ecriplus_avg_init, 2),
                "avg_final": round(ecriplus_avg_final, 2),
                "progression": round(ecriplus_progression, 2)
            }
        }
