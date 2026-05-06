import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.linear_model import LinearRegression
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from statsmodels.formula.api import ols

from app.models import AssessmentResult, Dictation, Student, Submission
from app.models.entities import Category


class StatsService:
    def __init__(self, session: Session):
        self.session = session

    def _group_rare_categories(
        self, df: pd.DataFrame, column: str, threshold: int = 5
    ) -> pd.Series:
        """
        Remplace les catégories qui apparaissent moins de 'threshold' fois par la valeur 'Autres'.
        """
        counts = df[column].value_counts()
        rare_cats = counts[counts < threshold].index
        return df[column].apply(lambda x: "Autres" if x in rare_cats else x)

    def get_rousseau_dashboard_stats(self) -> dict:
        students = self.session.exec(
            select(Student).options(
                selectinload(Student.promotion), selectinload(Student.group)
            )
        ).all()
        assessments = self.session.exec(select(AssessmentResult)).all()

        dictation = self.session.exec(select(Dictation)).first()
        dictation_text = (
            getattr(dictation, "content_reference", "") if dictation else ""
        )
        total_words = len(dictation_text.split()) if dictation_text else 1

        def to_precision(malus: float) -> float:
            return round(max(0.0, ((total_words - malus) / total_words) * 100), 2)

        def get_ass_name(enum_obj):
            return enum_obj.name if hasattr(enum_obj, "name") else str(enum_obj).upper()

        initial_scores = {}
        final_scores = {}

        for student in students:
            for sub in student.submissions:
                ass_name = get_ass_name(sub.assessment_type)

                if ass_name == "INITIAL" and sub.final_score is not None:
                    initial_scores[student.id] = to_precision(sub.final_score)
                elif ass_name == "FINAL" and sub.final_score is not None:
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
                if get_ass_name(a.assessment_type) == "INITIAL"
                and a.student.promotion
                and a.student.promotion.name == p_name
            ]
            vd2_f = [
                a.score
                for a in assessments
                if get_ass_name(a.assessment_type) == "FINAL"
                and a.student.promotion
                and a.student.promotion.name == p_name
            ]

            h1_final["dictation_initial"].append(safe_avg(vd1_i))
            h1_final["dictation_final"].append(safe_avg(vd1_f))
            h1_final["tools_initial"].append(safe_avg(vd2_i))
            h1_final["tools_final"].append(safe_avg(vd2_f))

            # H2
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

        all_groups = sorted(list(set(s.group.name for s in students if s.group)))
        h2_boxplots = {}

        for g_name in all_groups:
            g_st = [s for s in students if s.group and s.group.name == g_name]

            h2_boxplots[g_name] = {
                "initial": [
                    initial_scores[s.id] for s in g_st if s.id in initial_scores
                ],
                "final": [final_scores[s.id] for s in g_st if s.id in final_scores],
                "delta": [progressions[s.id] for s in g_st if s.id in progressions],
            }

        group_names = []
        delta_arrays = []

        for g_name, data in h2_boxplots.items():
            deltas = data["delta"]

            if len(deltas) >= 2:
                group_names.append(g_name)
                delta_arrays.append(deltas)

        anova_result = None
        tukey_results = []

        if len(delta_arrays) >= 2:
            f_stat, p_value = stats.f_oneway(*delta_arrays)
            is_significant = bool(p_value < 0.05)

            anova_result = {
                "f_stat": round(f_stat, 3),
                "p_value": round(p_value, 4),
                "is_significant": is_significant,
            }

            if is_significant:
                tukey = stats.tukey_hsd(*delta_arrays)
                for i in range(len(group_names)):
                    for j in range(i + 1, len(group_names)):
                        p_adj = tukey.pvalue[i, j]
                        if p_adj < 0.05:
                            mean_i = sum(delta_arrays[i]) / len(delta_arrays[i])
                            mean_j = sum(delta_arrays[j]) / len(delta_arrays[j])

                            better, worse = (
                                (group_names[i], group_names[j])
                                if mean_i > mean_j
                                else (group_names[j], group_names[i])
                            )

                            tukey_results.append(
                                {
                                    "group1": group_names[i],
                                    "group2": group_names[j],
                                    "p_value": round(p_adj, 4),
                                    "conclusion": f"Le groupe {better} a une progression significativement supérieure au groupe {worse}.",
                                }
                            )

        h2_stats_test = {"anova": anova_result, "tukey": tukey_results}

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
            t = h4_results[fam][cat].setdefault(
                lab, {"Initial": [], "Progress": [], "Effectif": 0}
            )

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

        # ANOVA Multifactorielle.
        anova_initial_results = []

        anova_data = []
        for s in students:
            if s.id in initial_scores:
                anova_data.append(
                    {
                        "InitialScore": initial_scores[s.id],
                        "CSP": str(get_val(s.parent_1_csp))
                        if s.parent_1_csp
                        else "Inconnu",
                        "Diplome": str(get_val(s.parent_1_degree))
                        if s.parent_1_degree
                        else "Inconnu",
                        "Appetence": f"Niveau_{s.appetence_level}"
                        if s.appetence_level
                        else "Inconnu",
                        "DeclaredLevel": f"Niveau_{s.declared_level}"
                        if s.declared_level
                        else "Inconnu",
                    }
                )

        df_anova = pd.DataFrame(anova_data)

        if len(anova_data) > 20:
            df_anova["CSP_grouped"] = self._group_rare_categories(
                df_anova, "CSP", threshold=8
            )
            df_anova["Diplome_grouped"] = self._group_rare_categories(
                df_anova, "Diplome", threshold=8
            )

        formula = "InitialScore ~ C(CSP_grouped) + C(Diplome_grouped) + C(Appetence) + C(DeclaredLevel)"

        try:
            model_anova = ols(formula, data=df_anova).fit()
            anova_table = sm.stats.anova_lm(model_anova, typ=2)

            anova_table["eta_sq"] = anova_table["sum_sq"] / sum(anova_table["sum_sq"])

            factors_to_check = [
                ("C(CSP_grouped)", "CSP"),
                ("C(Diplome_grouped)", "Diplôme"),
                ("C(Appetence)", "Appétence Lecture"),
                ("C(DeclaredLevel)", "Niveau Déclaré"),
            ]

            for table_key, display_name in factors_to_check:
                if table_key in anova_table.index:
                    p_val = anova_table.loc[table_key, "PR(>F)"]
                    eta_sq = anova_table.loc[table_key, "eta_sq"]

                    anova_initial_results.append(
                        {
                            "factor": display_name,
                            "p_value": round(p_val, 4),
                            "is_significant": bool(p_val < 0.05),
                            "impact_percent": round(eta_sq * 100, 1),
                        }
                    )

        except Exception as e:
            print(f"Erreur ANOVA : {e}")

        # Régression Multiple.
        regression_results = {"r2": 0, "coefficients": []}

        reg_data = []
        for s in students:
            if s.id in progressions and s.id in initial_scores:
                reg_data.append(
                    {
                        "Progression": progressions[s.id],
                        "Score Initial": initial_scores[s.id],
                        "Groupe": s.group.name if s.group else "Aucun",
                        "CSP": str(get_val(s.parent_1_csp))
                        if s.parent_1_csp
                        else "Inconnu",
                        "Diplôme": str(get_val(s.parent_1_degree))
                        if s.parent_1_degree
                        else "Inconnu",
                        "Niveau Lecture": f"Niveau {s.appetence_level}"
                        if s.appetence_level
                        else "Inconnu",
                        "Niveau Déclaré": f"Niveau {s.declared_level}"
                        if s.declared_level
                        else "Inconnu",
                    }
                )

        if len(reg_data) > 10:
            df = pd.DataFrame(reg_data)

            y = df["Progression"]
            X_raw = df.drop(columns=["Progression"])

            X = pd.get_dummies(X_raw, drop_first=False)

            model = LinearRegression()
            model.fit(X, y)

            r2 = round(model.score(X, y), 3)

            coefs = []
            for col, coef in zip(X.columns, model.coef_):
                if abs(coef) > 0.1:
                    coefs.append({"feature": col, "weight": round(coef, 2)})

            coefs = sorted(coefs, key=lambda x: x["weight"], reverse=True)

            regression_results = {"r2": r2, "coefficients": coefs}

        return {
            "h1_summary": h1_final,
            "h2_equivalence": h2_final,
            "h2_boxplots": h2_boxplots,
            "h2_stats_test": h2_stats_test,
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
            "regression_model": regression_results,
            "anova_multifactorial": anova_initial_results,
        }

    def get_emile_dashboard_stats(self) -> dict:
        students = self.session.exec(
            select(Student).options(
                selectinload(Student.promotion), selectinload(Student.group)
            )
        ).all()
        submissions = self.session.exec(
            select(Submission).options(
                selectinload(Submission.student).selectinload(Student.promotion),
                selectinload(Submission.student).selectinload(Student.group),
            )
        ).all()

        categories = self.session.exec(select(Category)).all()
        category_map = {c.id: c.name for c in categories}

        total_students = len(students)
        total_submissions = len(submissions)

        group_distribution_by_promo = {}
        for s in students:
            p_name = s.promotion.name if s.promotion else "Sans promo"
            g_name = s.group.name if s.group else "Sans groupe"

            if p_name not in group_distribution_by_promo:
                group_distribution_by_promo[p_name] = {}
            group_distribution_by_promo[p_name][g_name] = (
                group_distribution_by_promo[p_name].get(g_name, 0) + 1
            )

        promo_data = {}
        group_data = {}
        valid_final_scores = []

        tool_i_g2, tool_f_g2, tool_i_g5, tool_f_g5 = [], [], [], []
        hr_i_human, hr_f_human, hr_i_robot, hr_f_robot = [], [], [], []
        (
            mot_i_g1,
            mot_f_g1,
            mot_i_g2,
            mot_f_g2,
            mot_i_g3,
            mot_f_g3,
            mot_i_g4,
            mot_f_g4,
        ) = [], [], [], [], [], [], [], []

        mistakes_stats = {"global": {}, "promotions": {}}

        for sub in submissions:
            ass_type = (
                sub.assessment_type.name
                if hasattr(sub.assessment_type, "name")
                else str(sub.assessment_type).upper()
            )
            score = sub.final_score
            student = sub.student

            p_name = student.promotion.name if student.promotion else "Sans promo"
            g_code = student.group.name if student.group else "Sans groupe"

            if p_name not in promo_data:
                promo_data[p_name] = {"init": [], "fin": []}
            if g_code not in group_data:
                group_data[g_code] = {"init": [], "fin": []}

            if ass_type == "INITIAL":
                promo_data[p_name]["init"].append(score)
                group_data[g_code]["init"].append(score)

                if g_code == "G1":
                    mot_i_g1.append(score)
                elif g_code == "G2":
                    tool_i_g2.append(score)
                    hr_i_robot.append(score)
                    mot_i_g2.append(score)
                elif g_code == "G3":
                    hr_i_robot.append(score)
                    mot_i_g3.append(score)
                elif g_code == "G4":
                    hr_i_human.append(score)
                    mot_i_g4.append(score)
                elif g_code == "G5":
                    tool_i_g5.append(score)
                    hr_i_robot.append(score)

            elif ass_type == "FINAL":
                valid_final_scores.append(score)
                promo_data[p_name]["fin"].append(score)
                group_data[g_code]["fin"].append(score)

                if g_code == "G1":
                    mot_f_g1.append(score)
                elif g_code == "G2":
                    tool_f_g2.append(score)
                    hr_f_robot.append(score)
                    mot_f_g2.append(score)
                elif g_code == "G3":
                    hr_f_robot.append(score)
                    mot_f_g3.append(score)
                elif g_code == "G4":
                    hr_f_human.append(score)
                    mot_f_g4.append(score)
                elif g_code == "G5":
                    tool_f_g5.append(score)
                    hr_f_robot.append(score)

            if hasattr(sub, "mistakes") and sub.mistakes:
                if p_name not in mistakes_stats["promotions"]:
                    mistakes_stats["promotions"][p_name] = {}

                for mistake in sub.mistakes:
                    cat_name = category_map.get(mistake.category_id, "Non catégorisé")

                    t_rousseau = (
                        mistake.type_rousseau.value
                        if hasattr(mistake.type_rousseau, "value")
                        else str(mistake.type_rousseau)
                    )

                    if t_rousseau not in mistakes_stats["global"]:
                        mistakes_stats["global"][t_rousseau] = {}
                    mistakes_stats["global"][t_rousseau][cat_name] = (
                        mistakes_stats["global"][t_rousseau].get(cat_name, 0) + 1
                    )

                    if t_rousseau not in mistakes_stats["promotions"][p_name]:
                        mistakes_stats["promotions"][p_name][t_rousseau] = {}
                    mistakes_stats["promotions"][p_name][t_rousseau][cat_name] = (
                        mistakes_stats["promotions"][p_name][t_rousseau].get(
                            cat_name, 0
                        )
                        + 1
                    )

        def safe_avg(scores_list):
            return round(sum(scores_list) / len(scores_list), 2) if scores_list else 0.0

        def calc_progress(init_list, fin_list):
            if not init_list or not fin_list:
                return 0.0
            return round(safe_avg(init_list) - safe_avg(fin_list), 2)

        global_average = safe_avg(valid_final_scores)

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
            "group_distribution_by_promo": {
                promo: dict(sorted(groups.items()))
                for promo, groups in sorted(group_distribution_by_promo.items())
            },
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
                "Remédiation Humaine (G4)": {
                    "Initial": safe_avg(hr_i_human),
                    "Final": safe_avg(hr_f_human),
                },
                "Remédiation IA/Outil (G2, G3, G5)": {
                    "Initial": safe_avg(hr_i_robot),
                    "Final": safe_avg(hr_f_robot),
                },
            },
            "comparison_motivation": {
                "Autonomie (G1)": calc_progress(mot_i_g1, mot_f_g1),
                "Jalons obligatoires (G2)": calc_progress(mot_i_g2, mot_f_g2),
                "Salle (G3)": calc_progress(mot_i_g3, mot_f_g3),
                "Remédiation Humaine (G4)": calc_progress(mot_i_g4, mot_f_g4),
            },
            "mistakes_stats": mistakes_stats,
        }
