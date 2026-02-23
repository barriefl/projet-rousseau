from sqlmodel import Session, select
from app.models import AssessmentResult, AssessmentType, Group, Platform, Student, Submission
from sqlalchemy import Float, cast, func

class StatsService:
    def __init__(self, session: Session):
        self.session = session

    def _get_dictation_avg(self, a_type, group: Group = None) -> float:
        query = self.session.query(
            func.avg(
                cast(func.json_extract_path_text(Submission.scores, 'raw'), Float)
            )
        ).filter(Submission.assessment_type == a_type)

        if group:
            query = query.join(Student).filter(Student.group == group)
        
        result = query.scalar()
        return result or 0.0
    
    def _get_platform_avg(self, platform: Platform, a_type: AssessmentType, group: Group = None) -> float:
        query = self.session.query(func.avg(AssessmentResult.score))\
            .filter(AssessmentResult.platform == platform)\
            .filter(AssessmentResult.assessment_type == a_type)

        if group:
            query = query.join(Student).filter(Student.group == group)

        result = query.scalar()
        return result or 0.0

    def get_global_kpis(self):
        """Récupère les indicateurs clés globaux."""

        total_students = self.session.query(Student).count()
        total_submissions = self.session.query(Submission).count()
        total_voltaire_assessments = self.session.query(AssessmentResult)\
            .filter(AssessmentResult.platform == Platform.VOLTAIRE)\
            .count()
        total_ecriplus_assessments = self.session.query(AssessmentResult)\
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
        
        active_groups = self.session.query(Student.group)\
            .distinct()\
            .filter(Student.group.isnot(None))\
            .order_by(Student.group)\
            .all()
        
        group_data = {}
        
        for (grp_enum,) in active_groups:
            if not grp_enum: continue

            student_count = self.session.query(Student).filter(Student.group == grp_enum).count()

            sub_count = self.session.query(Submission).join(Student)\
                .filter(Student.group == grp_enum).count()
            
            d_init = self._get_dictation_avg(AssessmentType.INITIAL, group=grp_enum)
            d_final = self._get_dictation_avg(AssessmentType.FINAL, group=grp_enum)

            dictations_data = {
                "total": sub_count,
                "avg_init": round(d_init, 2),
                "avg_final": round(d_final, 2),
                "progression": round(d_final - d_init, 2)
            }

            volt_count = self.session.query(AssessmentResult).join(Student)\
                .filter(Student.group == grp_enum, AssessmentResult.platform == Platform.VOLTAIRE).count()
            
            ecri_count = self.session.query(AssessmentResult).join(Student)\
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
    
    def get_emile_dashboard_stats(self) -> dict:
        students = self.session.exec(select(Student)).all()
        submissions = self.session.exec(select(Submission)).all()
        final_submissions = [sub for sub in submissions if sub.assessment_type.name == "FINAL" and sub.final_score is not None]

        total_students = len(students)
        total_submissions = len(submissions)

        group_distribution = {}
        for s in students:
            g_name = s.group.value if s.group else "Sans groupe"
            group_distribution[g_name] = group_distribution.get(g_name, 0) + 1

        global_average = 0.0
        if final_submissions:
            global_average = round(sum(sub.final_score for sub in final_submissions) / len(final_submissions), 2)

        group_scores = {}
        promo_scores = {}
        for sub in final_submissions:
            if sub.student:
                promo_name = sub.student.promo or "Sans promo"
                if promo_name not in promo_scores:
                    promo_scores[promo_name] = []
                promo_scores[promo_name].append(sub.final_score)

                if sub.student.group:
                    g_name = sub.student.group.value
                    if g_name not in group_scores:
                        group_scores[g_name] = []
                    group_scores[g_name].append(sub.final_score)

        group_averages = {g: round(sum(scores) / len(scores), 2) for g, scores in group_scores.items()}
        promo_averages = {p: round(sum(scores) / len(scores), 2) for p, scores in promo_scores.items()}

        sorted_group_distribution = dict(sorted(group_distribution.items()))
        sorted_group_averages = dict(sorted(group_averages.items()))
        sorted_promo_averages = dict(sorted(promo_averages.items()))

        tool_g2, tool_g5 = [], []
        hr_human, hr_robot = [], []
        mot_g1, mot_g2, mot_g3 = [], [], []

        for sub in final_submissions:
            if sub.student and sub.student.group:
                g_code = sub.student.group.name

                if g_code == "G2": tool_g2.append(sub.final_score)
                elif g_code == "G5": tool_g5.append(sub.final_score)

                if g_code == "G4": hr_human.append(sub.final_score)
                elif g_code in ["G2", "G3", "G5"]: hr_robot.append(sub.final_score)

                if g_code == "G1": mot_g1.append(sub.final_score)
                elif g_code == "G2": mot_g2.append(sub.final_score)
                elif g_code == "G3": mot_g3.append(sub.final_score)

        def safe_avg(scores_list):
            return round(sum(scores_list) / len(scores_list), 2) if scores_list else 0.0

        return {
            "total_students": total_students,
            "total_submissions": total_submissions,
            "global_average": global_average,
            "group_distribution": sorted_group_distribution,
            "group_averages": sorted_group_averages,
            "promo_averages": sorted_promo_averages,
            "comparison_tool": {
                "Projet Voltaire (G2)": safe_avg(tool_g2),
                "Écri+ (G5)": safe_avg(tool_g5)
            },
            "comparison_human_robot": {
                "Correction Humaine (G4)": safe_avg(hr_human),
                "Correction IA/Outil (G2, G3, G5)": safe_avg(hr_robot)
            },
            "comparison_motivation": {
                "Autonomie (G1)": safe_avg(mot_g1),
                "Jalons obligatoires (G2)": safe_avg(mot_g2),
                "Salle (G3)": safe_avg(mot_g3)
            }
        }