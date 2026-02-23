from sqlmodel import Session, select
from app.models import AssessmentResult, Student, Submission

class StatsService:
    def __init__(self, session: Session):
        self.session = session

    def get_rousseau_dashboard_stats(self) -> dict:
        students = self.session.exec(select(Student)).all()
        assessments = self.session.exec(select(AssessmentResult)).all()
        
        initial_scores = {}
        final_scores = {}
        
        for student in students:
            for sub in student.submissions:
                if sub.assessment_type.name == "INITIAL" and sub.final_score is not None:
                    initial_scores[student.id] = sub.final_score
                elif sub.assessment_type.name == "FINAL" and sub.final_score is not None:
                    final_scores[student.id] = sub.final_score

        initial_g0_g4 = [
            score for s_id, score in initial_scores.items() 
            if any(s.id == s_id and s.group and s.group.name != "G5" for s in students)
        ]
        avg_initial_g0_g4 = sum(initial_g0_g4) / len(initial_g0_g4) if initial_g0_g4 else 0.0

        progressions = {}
        for s in students:
            if s.id in final_scores:
                f_score = final_scores[s.id]
                if s.group and s.group.name == "G5" and s.id not in initial_scores:
                    i_score = avg_initial_g0_g4
                else:
                    i_score = initial_scores.get(s.id)
                
                if i_score is not None:
                    progressions[s.id] = f_score - i_score

        def safe_avg(scores_list):
            return round(sum(scores_list) / len(scores_list), 2) if scores_list else 0.0

        # --- HYPOTHÈSE 1 : Outils (VD2) vs Dictées (VD1). ---
        vd1_initial_vals = [
            initial_scores.get(s.id, avg_initial_g0_g4 if (s.group and s.group.name == "G5") else None) 
            for s in students if s.group and s.group.name != "G0" and s.id in final_scores
        ]
        vd1_final_vals = [
            final_scores[s.id] for s in students if s.group and s.group.name != "G0" and s.id in final_scores
        ]

        vd2_initial_vals = [a.score for a in assessments if a.assessment_type.name == "INITIAL" and a.student.group.name != "G0"]
        vd2_final_vals = [a.score for a in assessments if a.assessment_type.name == "FINAL" and a.student.group.name != "G0"]

        vd1_initial_vals = [v for v in vd1_initial_vals if v is not None]

        # --- HYPOTHÈSE 2 : Équivalence G2 vs G5. ---
        final_g2 = [final_scores[s.id] for s in students if s.group and s.group.name == "G2" and s.id in final_scores]
        final_g5 = [final_scores[s.id] for s in students if s.group and s.group.name == "G5" and s.id in final_scores]

        # --- HYPOTHÈSE 3 : Facteur Enseignant (G4 vs Autres G2/G3/G5). ---
        final_g4 = [final_scores[s.id] for s in students if s.group and s.group.name == "G4" and s.id in final_scores]
        final_others = [final_scores[s.id] for s in students if s.group and s.group.name in ["G2", "G3", "G5"] and s.id in final_scores]

        # --- HYPOTHÈSE 4 : Socioculturel (Lecture vs Progression). ---
        categories = {
            "Appétence à la lecture": {},
            "Présence d'une bibliothèque": {},
            "Support de lecture": {},
            "CSP Parent 1": {},
            "Degree Parent 1": {},
            "CSP Parent 2": {},
            "Degree Parent 2": {},
            "Niveau déclaré": {}
        }
        
        for s in students:
            if s.id in progressions:
                prog = progressions[s.id]
                
                # 1. Appétence.
                app = s.appetence_level if getattr(s, 'appetence_level', None) else "Non renseigné"
                categories["Appétence à la lecture"].setdefault(f"Niveau {app}" if app != "Non renseigné" else app, []).append(prog)
                
                # 2. Bibliothèque.
                bib = s.has_library.value if getattr(s, 'has_library', None) else "Non renseigné"
                categories["Présence d'une bibliothèque"].setdefault(str(bib), []).append(prog)
                
                # 3. Support.
                sup = s.reading_support.value if getattr(s, 'reading_support', None) else "Non renseigné"
                categories["Support de lecture"].setdefault(str(sup), []).append(prog)
                
                # 4. CSP Parent 1.
                csp = s.parent_1_csp.value if getattr(s, 'parent_1_csp', None) else "Non renseigné"
                categories["CSP Parent 1"].setdefault(str(csp), []).append(prog)

                # 5. Degree Parent 1.
                degree = s.parent_1_degree.value if getattr(s, 'parent_1_degree', None) else "Non renseigné"
                categories["Degree Parent 1"].setdefault(str(degree), []).append(prog)

                # 6. CSP Parent 2.
                csp = s.parent_2_csp.value if getattr(s, 'parent_2_csp', None) else "Non renseigné"
                categories["CSP Parent 2"].setdefault(str(csp), []).append(prog)

                # 7. Degree Parent 2.
                degree = s.parent_2_degree.value if getattr(s, 'parent_2_degree', None) else "Non renseigné"
                categories["Degree Parent 2"].setdefault(str(degree), []).append(prog)

                # 8. Niveau déclaré.
                niv = s.declared_level if getattr(s, 'declared_level', None) else "Non renseigné"
                categories["Niveau déclaré"].setdefault(f"Niveau {niv}" if niv != "Non renseigné" else niv, []).append(prog)

        sociocultural_impact = {}
        for cat_name, val_dict in categories.items():
            sociocultural_impact[cat_name] = {
                k: safe_avg(v) for k, v in sorted(val_dict.items())
            }

        return {
            "tools_vs_dictation": {
                "VD1 (Dictées - Moyenne malus)": {
                    "Initial": safe_avg(vd1_initial_vals),
                    "Final": safe_avg(vd1_final_vals)
                },
                "VD2 (Outils - Score)": {
                    "Initial": safe_avg(vd2_initial_vals),
                    "Final": safe_avg(vd2_final_vals)
                }
            },
            "equivalence_g2_g5": {
                "Score Final G2": safe_avg(final_g2),
                "Score Final G5": safe_avg(final_g5)
            },
            "teacher_factor": {
                "Accompagnement Humain (G4)": safe_avg(final_g4),
                "Autonomie / Outils (G2, G3, G5)": safe_avg(final_others)
            },
            "sociocultural_impact": sociocultural_impact
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