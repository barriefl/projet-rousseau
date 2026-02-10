from app.models import AssessmentResult, AssessmentType, Group, Platform, Student, Submission
from sqlalchemy import Float, cast, func
from sqlalchemy.orm import Session

class StatsService:
    def __init__(self, db: Session):
        self.db = db

    def _get_dictation_avg(self, a_type, group: Group = None) -> float:
        query = self.db.query(
            func.avg(
                cast(func.json_extract_path_text(Submission.scores, 'raw'), Float)
            )
        ).filter(Submission.assessment_type == a_type)

        if group:
            query = query.join(Student).filter(Student.group == group)
        
        result = query.scalar()
        return result or 0.0
    
    def _get_platform_avg(self, platform: Platform, a_type: AssessmentType, group: Group = None) -> float:
        query = self.db.query(func.avg(AssessmentResult.score))\
            .filter(AssessmentResult.platform == platform)\
            .filter(AssessmentResult.assessment_type == a_type)

        if group:
            query = query.join(Student).filter(Student.group == group)

        result = query.scalar()
        return result or 0.0

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

        submissions_avg_init = self._get_dictation_avg(AssessmentType.INITIAL)
        submissions_avg_final = self._get_dictation_avg(AssessmentType.FINAL)
        
        voltaire_avg_init = self._get_platform_avg(Platform.VOLTAIRE, AssessmentType.INITIAL)
        voltaire_avg_final = self._get_platform_avg(Platform.VOLTAIRE, AssessmentType.FINAL)

        ecriplus_avg_init = self._get_platform_avg(Platform.ECRIPLUS, AssessmentType.INITIAL)
        ecriplus_avg_final = self._get_platform_avg(Platform.ECRIPLUS, AssessmentType.FINAL)

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
    
    def get_group_stats(self):
        """Récupère les statistiques détaillées par groupe de manière dynamique et triée."""
        
        active_groups = self.db.query(Student.group)\
            .distinct()\
            .filter(Student.group.isnot(None))\
            .order_by(Student.group)\
            .all()
        
        group_data = {}
        
        for (grp_enum,) in active_groups:
            if not grp_enum: continue

            student_count = self.db.query(Student).filter(Student.group == grp_enum).count()

            sub_count = self.db.query(Submission).join(Student)\
                .filter(Student.group == grp_enum).count()
            
            d_init = self._get_dictation_avg(AssessmentType.INITIAL, group=grp_enum)
            d_final = self._get_dictation_avg(AssessmentType.FINAL, group=grp_enum)

            dictations_data = {
                "total": sub_count,
                "avg_init": round(d_init, 2),
                "avg_final": round(d_final, 2),
                "progression": round(d_final - d_init, 2)
            }

            volt_count = self.db.query(AssessmentResult).join(Student)\
                .filter(Student.group == grp_enum, AssessmentResult.platform == Platform.VOLTAIRE).count()
            
            ecri_count = self.db.query(AssessmentResult).join(Student)\
                .filter(Student.group == grp_enum, AssessmentResult.platform == Platform.ECRIPLUS).count()

            external_data = None

            if volt_count == 0 and ecri_count == 0:
                external_data = None
            
            elif volt_count >= ecri_count:
                v_init = self._get_platform_avg(Platform.VOLTAIRE, AssessmentType.INITIAL, group=grp_enum)
                v_final = self._get_platform_avg(Platform.VOLTAIRE, AssessmentType.FINAL, group=grp_enum)
                external_data = {
                    "platform_name": "Voltaire",
                    "total": volt_count,
                    "avg_init": round(v_init, 2),
                    "avg_final": round(v_final, 2),
                    "progression": round(v_final - v_init, 2)
                }

            else:
                e_init = self._get_platform_avg(Platform.ECRIPLUS, AssessmentType.INITIAL, group=grp_enum)
                e_final = self._get_platform_avg(Platform.ECRIPLUS, AssessmentType.FINAL, group=grp_enum)
                external_data = {
                    "platform_name": "Ecri+",
                    "total": ecri_count,
                    "avg_init": round(e_init, 2),
                    "avg_final": round(e_final, 2),
                    "progression": round(e_final - e_init, 2)
                }

            group_data[grp_enum.value] = {
                "student_count": student_count,
                "dictations": dictations_data,
                "external_assessment": external_data
            }

        return {
            "total_groups": len(active_groups),
            "groups": group_data
        }