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
            "CSP Parents": {},
            "Diplôme Parents": {},
            "Niveau déclaré": {},
            "Œuvres lues": {},
            "Motifs de lecture": {}
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
                
                # 4. CSP Parents.
                csps = set()
                if getattr(s, 'parent_1_csp', None): csps.add(s.parent_1_csp.value)
                if getattr(s, 'parent_2_csp', None): csps.add(s.parent_2_csp.value)
                
                if not csps:
                    categories["CSP Parents"].setdefault("Non renseigné", []).append(prog)
                else:
                    for csp in csps:
                        categories["CSP Parents"].setdefault(str(csp), []).append(prog)

                # 5. Degree Parents.
                degrees = set()
                if getattr(s, 'parent_1_degree', None): degrees.add(s.parent_1_degree.value)
                if getattr(s, 'parent_2_degree', None): degrees.add(s.parent_2_degree.value)
                
                if not degrees:
                    categories["Diplôme Parents"].setdefault("Non renseigné", []).append(prog)
                else:
                    for degree in degrees:
                        categories["Diplôme Parents"].setdefault(str(degree), []).append(prog)

                # 6. Niveau déclaré.
                niv = s.declared_level if getattr(s, 'declared_level', None) else "Non renseigné"
                categories["Niveau déclaré"].setdefault(f"Niveau {niv}" if niv != "Non renseigné" else niv, []).append(prog)

                # 7. Œuvres lues.
                rw_val = getattr(s, 'reading_works', None)
                if rw_val:
                    works = [w.strip() for w in rw_val.split(';') if w.strip()]
                    if works:
                        for w in works:
                            categories["Œuvres lues"].setdefault(w, []).append(prog)
                    else:
                        categories["Œuvres lues"].setdefault("Non renseigné", []).append(prog)
                else:
                    categories["Œuvres lues"].setdefault("Non renseigné", []).append(prog)

                # 8. Motif de lecture.
                mot_val = getattr(s, 'motive', None)
                if mot_val:
                    motives = [m.strip() for m in mot_val.split(';') if m.strip()]
                    if motives:
                        for m in motives:
                            categories["Motifs de lecture"].setdefault(m, []).append(prog)
                    else:
                        categories["Motifs de lecture"].setdefault("Non renseigné", []).append(prog)
                else:
                    categories["Motifs de lecture"].setdefault("Non renseigné", []).append(prog)

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

        total_students = len(students)
        total_submissions = len(submissions)

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

        group_distribution = {}
        for s in students:
            g_name = s.group.value if s.group else "Sans groupe"
            group_distribution[g_name] = group_distribution.get(g_name, 0) + 1

        valid_final_scores = list(final_scores.values())
        global_average = round(sum(valid_final_scores) / len(valid_final_scores), 2) if valid_final_scores else 0.0

        promo_data = {}
        group_data = {}

        tool_i_g2, tool_f_g2, tool_i_g5, tool_f_g5 = [], [], [], []
        hr_i_human, hr_f_human, hr_i_robot, hr_f_robot = [], [], [], []
        mot_i_g1, mot_f_g1, mot_i_g2, mot_f_g2, mot_i_g3, mot_f_g3 = [], [], [], [], [], []

        for s in [st for st in students if st.id in final_scores]:
            f_score = final_scores[s.id]
            i_score = initial_scores.get(s.id)
            
            if i_score is None and s.group and s.group.name == "G5":
                i_score = avg_initial_g0_g4

            p_name = s.promo or "Sans promo"
            if p_name not in promo_data:
                promo_data[p_name] = {"init": [], "fin": []}
            if i_score is not None: promo_data[p_name]["init"].append(i_score)
            promo_data[p_name]["fin"].append(f_score)

            if s.group:
                g_val = s.group.value
                g_code = s.group.name
                
                if g_val not in group_data:
                    group_data[g_val] = {"init": [], "fin": []}
                if i_score is not None: group_data[g_val]["init"].append(i_score)
                group_data[g_val]["fin"].append(f_score)

                if g_code == "G2":
                    if i_score is not None: tool_i_g2.append(i_score)
                    tool_f_g2.append(f_score)
                elif g_code == "G5":
                    if i_score is not None: tool_i_g5.append(i_score)
                    tool_f_g5.append(f_score)

                if g_code == "G4":
                    if i_score is not None: hr_i_human.append(i_score)
                    hr_f_human.append(f_score)
                elif g_code in ["G2", "G3", "G5"]:
                    if i_score is not None: hr_i_robot.append(i_score)
                    hr_f_robot.append(f_score)

                if g_code == "G1":
                    if i_score is not None: mot_i_g1.append(i_score)
                    mot_f_g1.append(f_score)
                elif g_code == "G2":
                    if i_score is not None: mot_i_g2.append(i_score)
                    mot_f_g2.append(f_score)
                elif g_code == "G3":
                    if i_score is not None: mot_i_g3.append(i_score)
                    mot_f_g3.append(f_score)

        def safe_avg(scores_list):
            return round(sum(scores_list) / len(scores_list), 2) if scores_list else 0.0

        promo_averages = {
            p: {"Initial": safe_avg(data["init"]), "Final": safe_avg(data["fin"])}
            for p, data in promo_data.items()
        }
        
        group_averages = {
            g: {"Initial": safe_avg(data["init"]), "Final": safe_avg(data["fin"])}
            for g, data in group_data.items()
        }

        return {
            "total_students": total_students,
            "total_submissions": total_submissions,
            "global_average": global_average,
            "group_distribution": dict(sorted(group_distribution.items())),
            "group_averages": dict(sorted(group_averages.items())),
            "promo_averages": dict(sorted(promo_averages.items())),
            
            "comparison_tool": {
                "Projet Voltaire (G2)": {"Initial": safe_avg(tool_i_g2), "Final": safe_avg(tool_f_g2)},
                "Écri+ (G5)": {"Initial": safe_avg(tool_i_g5), "Final": safe_avg(tool_f_g5)}
            },
            "comparison_human_robot": {
                "Correction Humaine (G4)": {"Initial": safe_avg(hr_i_human), "Final": safe_avg(hr_f_human)},
                "Correction IA/Outil (G2, G3, G5)": {"Initial": safe_avg(hr_i_robot), "Final": safe_avg(hr_f_robot)}
            },
            "comparison_motivation": {
                "Autonomie (G1)": {"Initial": safe_avg(mot_i_g1), "Final": safe_avg(mot_f_g1)},
                "Jalons obligatoires (G2)": {"Initial": safe_avg(mot_i_g2), "Final": safe_avg(mot_f_g2)},
                "Salle (G3)": {"Initial": safe_avg(mot_i_g3), "Final": safe_avg(mot_f_g3)}
            }
        }