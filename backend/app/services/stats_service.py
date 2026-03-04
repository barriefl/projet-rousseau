from sqlmodel import Session, select

from app.models import AssessmentResult, AssessmentType, Dictation, Student, Submission


class StatsService:
    def __init__(self, session: Session):
        self.session = session

    def get_rousseau_dashboard_stats(self) -> dict:
        students = self.session.exec(select(Student)).all()
        assessments = self.session.exec(select(AssessmentResult)).all()

        dictation = self.session.exec(select(Dictation)).first()
        dictation_text = (
            getattr(dictation, "content_reference", "") if dictation else ""
        )
        total_words = len(dictation_text.split()) if dictation_text else 1

        def to_precision(malus: float) -> float:
            if malus is None:
                return 0.0
            return round(max(0.0, ((total_words - malus) / total_words) * 100), 2)

        initial_scores = {}
        final_scores = {}

        for student in students:
            for sub in student.submissions:
                if (
                    sub.assessment_type == AssessmentType.INITIAL
                    and sub.final_score is not None
                ):
                    initial_scores[student.id] = to_precision(sub.final_score)
                elif (
                    sub.assessment_type == AssessmentType.FINAL
                    and sub.final_score is not None
                ):
                    final_scores[student.id] = to_precision(sub.final_score)

        progressions = {}
        for s in students:
            if s.id in final_scores and s.id in initial_scores:
                progressions[s.id] = round(final_scores[s.id] - initial_scores[s.id], 2)

        def safe_avg(scores):
            return round(sum(scores) / len(scores), 2) if scores else 0.0

        def get_val(enum_member):
            return enum_member.value if hasattr(enum_member, "value") else enum_member

        promotions = sorted(
            list(set(s.promotion.name for s in students if s.promotion))
        )

        h1_final = {
            "labels": promotions,
            "dictation_initial": [],
            "dictation_final": [],
            "tools_initial": [],
            "tools_final": [],
            "effectif": [],
        }

        h2_final = {
            "labels": promotions,
            "g2_final": [],
            "g2_progress": [],
            "g5_final": [],
            "g5_progress": [],
            "effectif": [],
        }

        for p_name in promotions:
            promo_students = [
                s for s in students if s.promotion and s.promotion.name == p_name
            ]
            h1_final["effectif"].append(len(promo_students))
            h2_final["effectif"].append(len(promo_students))

            p_st = [
                s
                for s in students
                if s.promotion and s.promotion.name == p_name and s.id in final_scores
            ]

            vd1_i = [
                initial_scores.get(s.id)
                for s in p_st
                if s.group and s.group.name != "G0"
            ]
            vd1_i = [v for v in vd1_i if v is not None]

            vd1_f = [
                final_scores[s.id] for s in p_st if s.group and s.group.name != "G0"
            ]

            vd2_i = [
                a.score
                for a in assessments
                if a.assessment_type == AssessmentType.INITIAL
                and a.student.promotion
                and a.student.promotion.name == p_name
            ]
            vd2_f = [
                a.score
                for a in assessments
                if a.assessment_type == AssessmentType.FINAL
                and a.student.promotion
                and a.student.promotion.name == p_name
            ]

            h1_final["dictation_initial"].append(safe_avg(vd1_i))
            h1_final["dictation_final"].append(safe_avg(vd1_f))
            h1_final["tools_initial"].append(safe_avg(vd2_i))
            h1_final["tools_final"].append(safe_avg(vd2_f))

            # H2 : Progression stricte
            g2_s = [
                final_scores[s.id] for s in p_st if s.group and s.group.name == "G2"
            ]
            g2_p = [
                progressions[s.id]
                for s in p_st
                if s.group and s.group.name == "G2" and s.id in progressions
            ]
            g5_s = [
                final_scores[s.id] for s in p_st if s.group and s.group.name == "G5"
            ]
            g5_p = [
                progressions[s.id]
                for s in p_st
                if s.group and s.group.name == "G5" and s.id in progressions
            ]

            h2_final["g2_final"].append(safe_avg(g2_s))
            h2_final["g2_progress"].append(safe_avg(g2_p))
            h2_final["g5_final"].append(safe_avg(g5_s))
            h2_final["g5_progress"].append(safe_avg(g5_p))

        # H3
        total_g4 = len([s for s in students if s.group and s.group.name == "G4"])
        total_auto = len(
            [s for s in students if s.group and s.group.name in ["G2", "G3", "G5"]]
        )

        f_g4 = [
            final_scores[s.id]
            for s in students
            if s.id in final_scores and s.group and s.group.name == "G4"
        ]
        f_auto = [
            final_scores[s.id]
            for s in students
            if s.id in final_scores and s.group and s.group.name in ["G2", "G3", "G5"]
        ]

        # H4
        h4_results = {
            "Catégorie socio-culturelle": {"CSP Parents": {}, "Diplôme Parents": {}},
            "Pratique de la lecture": {
                "Appétence": {},
                "Bibliothèque": {},
                "Support": {},
                "Œuvres lues": {},
                "Motifs": {},
            },
            "Orthographe, grammaire, conjugaison": {"Niveau déclaré": {}},
        }

        def add_s(fam, cat, lab, s_id):
            if not lab or lab == "None":
                lab = "Non renseigné"
            t = h4_results[fam][cat].setdefault(lab, {"Initial": [], "Progress": [], "Effectif": 0})

            t["Effectif"] += 1

            if s_id in initial_scores:
                t["Initial"].append(initial_scores[s_id])
            if s_id in progressions:
                t["Progress"].append(progressions[s_id])

        for s in students:
            for csp in filter(None, {get_val(s.parent_1_csp), get_val(s.parent_2_csp)}):
                add_s("Catégorie socio-culturelle", "CSP Parents", str(csp), s.id)
            for deg in filter(
                None, {get_val(s.parent_1_degree), get_val(s.parent_2_degree)}
            ):
                add_s("Catégorie socio-culturelle", "Diplôme Parents", str(deg), s.id)
            add_s(
                "Pratique de la lecture",
                "Appétence",
                f"Niveau {s.appetence_level}" if s.appetence_level else None,
                s.id,
            )
            add_s(
                "Pratique de la lecture", "Bibliothèque", get_val(s.has_library), s.id
            )
            add_s("Pratique de la lecture", "Support", get_val(s.reading_support), s.id)
            if s.reading_works:
                for w in s.reading_works.split(";"):
                    add_s("Pratique de la lecture", "Œuvres lues", w.strip(), s.id)
            if s.motive:
                for m in s.motive.split(";"):
                    add_s("Pratique de la lecture", "Motifs", m.strip(), s.id)
            add_s(
                "Orthographe, grammaire, conjugaison",
                "Niveau déclaré",
                f"Niveau {s.declared_level}" if s.declared_level else None,
                s.id,
            )

        h4_final = {}
        NIVEAU_ORDER = {
            "Niveau Mauvais": 0,
            "Niveau 1": 1,
            "Niveau 2": 2,
            "Niveau 3": 3,
            "Niveau 4": 4,
            "Niveau 5": 5,
            "Niveau Excellent": 6,
        }

        for family, categories in h4_results.items():
            h4_final[family] = {}
            for cat, data in categories.items():
                items = list(data.items())

                if cat in ["Appétence", "Niveau déclaré"]:
                    items.sort(key=lambda x: NIVEAU_ORDER.get(x[0], 90))
                else:
                    items.sort(key=lambda x: safe_avg(x[1]["Progress"]), reverse=True)

                h4_final[family][cat] = {
                    str(label): {
                        "Initial": float(safe_avg(v["Initial"])),
                        "Progress": float(safe_avg(v["Progress"])),
                        "Effectif": int(v["Effectif"]),
                    }
                    for label, v in items
                }

        return {
            "h1_summary": h1_final,
            "h2_equivalence": h2_final,
            "h3_teacher": {
                "Accompagnement Humain (G4)": {
                    "score": safe_avg(f_g4),
                    "effectif": total_g4,
                },
                "Autonomie / Outils (G2/G3/G5)": {
                    "score": safe_avg(f_auto),
                    "effectif": total_auto,
                },
            },
            "h4_sociocultural": h4_final,
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
                if (
                    sub.assessment_type.name == "INITIAL"
                    and sub.final_score is not None
                ):
                    initial_scores[student.id] = sub.final_score
                elif (
                    sub.assessment_type.name == "FINAL" and sub.final_score is not None
                ):
                    final_scores[student.id] = sub.final_score

        initial_g0_g4 = [
            score
            for s_id, score in initial_scores.items()
            if any(s.id == s_id and s.group and s.group.name != "G5" for s in students)
        ]
        avg_initial_g0_g4 = (
            sum(initial_g0_g4) / len(initial_g0_g4) if initial_g0_g4 else 0.0
        )

        group_distribution = {}
        for s in students:
            g_name = s.group.value if s.group else "Sans groupe"
            group_distribution[g_name] = group_distribution.get(g_name, 0) + 1

        valid_final_scores = list(final_scores.values())
        global_average = (
            round(sum(valid_final_scores) / len(valid_final_scores), 2)
            if valid_final_scores
            else 0.0
        )

        promo_data = {}
        group_data = {}

        tool_i_g2, tool_f_g2, tool_i_g5, tool_f_g5 = [], [], [], []
        hr_i_human, hr_f_human, hr_i_robot, hr_f_robot = [], [], [], []
        mot_i_g1, mot_f_g1, mot_i_g2, mot_f_g2, mot_i_g3, mot_f_g3 = (
            [],
            [],
            [],
            [],
            [],
            [],
        )

        for s in [st for st in students if st.id in final_scores]:
            f_score = final_scores[s.id]
            i_score = initial_scores.get(s.id)

            if i_score is None and s.group and s.group.name == "G5":
                i_score = avg_initial_g0_g4

            p_name = s.promo or "Sans promo"
            if p_name not in promo_data:
                promo_data[p_name] = {"init": [], "fin": []}
            if i_score is not None:
                promo_data[p_name]["init"].append(i_score)
            promo_data[p_name]["fin"].append(f_score)

            if s.group:
                g_val = s.group.value
                g_code = s.group.name

                if g_val not in group_data:
                    group_data[g_val] = {"init": [], "fin": []}
                if i_score is not None:
                    group_data[g_val]["init"].append(i_score)
                group_data[g_val]["fin"].append(f_score)

                if g_code == "G2":
                    if i_score is not None:
                        tool_i_g2.append(i_score)
                    tool_f_g2.append(f_score)
                elif g_code == "G5":
                    if i_score is not None:
                        tool_i_g5.append(i_score)
                    tool_f_g5.append(f_score)

                if g_code == "G4":
                    if i_score is not None:
                        hr_i_human.append(i_score)
                    hr_f_human.append(f_score)
                elif g_code in ["G2", "G3", "G5"]:
                    if i_score is not None:
                        hr_i_robot.append(i_score)
                    hr_f_robot.append(f_score)

                if g_code == "G1":
                    if i_score is not None:
                        mot_i_g1.append(i_score)
                    mot_f_g1.append(f_score)
                elif g_code == "G2":
                    if i_score is not None:
                        mot_i_g2.append(i_score)
                    mot_f_g2.append(f_score)
                elif g_code == "G3":
                    if i_score is not None:
                        mot_i_g3.append(i_score)
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
                "Projet Voltaire (G2)": {
                    "Initial": safe_avg(tool_i_g2),
                    "Final": safe_avg(tool_f_g2),
                },
                "Écri+ (G5)": {
                    "Initial": safe_avg(tool_i_g5),
                    "Final": safe_avg(tool_f_g5),
                },
            },
            "comparison_human_robot": {
                "Correction Humaine (G4)": {
                    "Initial": safe_avg(hr_i_human),
                    "Final": safe_avg(hr_f_human),
                },
                "Correction IA/Outil (G2, G3, G5)": {
                    "Initial": safe_avg(hr_i_robot),
                    "Final": safe_avg(hr_f_robot),
                },
            },
            "comparison_motivation": {
                "Autonomie (G1)": {
                    "Initial": safe_avg(mot_i_g1),
                    "Final": safe_avg(mot_f_g1),
                },
                "Jalons obligatoires (G2)": {
                    "Initial": safe_avg(mot_i_g2),
                    "Final": safe_avg(mot_f_g2),
                },
                "Salle (G3)": {
                    "Initial": safe_avg(mot_i_g3),
                    "Final": safe_avg(mot_f_g3),
                },
            },
        }
