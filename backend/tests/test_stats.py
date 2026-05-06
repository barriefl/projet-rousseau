import uuid

from fastapi import status
from sqlmodel import Session

from app.endpoints.stats_endpoint import get_stats_service
from app.main import app
from app.models.entities import (
    AssessmentResult,
    Category,
    Dictation,
    Group,
    Mistake,
    Promotion,
    Student,
    Submission,
    Tool,
)
from app.models.enums import CSP, AssessmentType, Degree, MistakeType


# ---------------------------------------------------------
# TEST DE BASE (200 OK).
# ---------------------------------------------------------
def test_get_rousseau_stats_empty_db(auth_client):
    """
    Vérifie que l'endpoint Rousseau renvoie un 200 OK et une structure JSON valide (avec des listes vides) quand il n'y a aucun étudiant.
    """

    # ACT.
    response = auth_client.get("/api/stats/rousseau")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK, (
        f"Erreur de l'API: {response.text}"
    )

    data = response.json()

    expected_empty_state = {
        "h1_summary": {
            "labels": [],
            "dictation_initial": [],
            "dictation_final": [],
            "tools_initial": [],
            "tools_final": [],
            "effectif": [],
        },
        "h2_equivalence": {
            "labels": [],
            "g2_final": [],
            "g2_progress": [],
            "g5_final": [],
            "g5_progress": [],
            "effectif": [],
        },
        "h2_boxplots": {},
        "h2_stats_test": {"anova": None, "tukey": []},
        "h3_teacher": {
            "Accompagnement Humain (G4)": {"score": 0.0, "effectif": 0},
            "Autonomie / Outils (G2/G3/G5)": {"score": 0.0, "effectif": 0},
        },
        "h4_sociocultural": {
            "Catégorie socio-culturelle": {"CSP Parents": {}, "Diplôme Parents": {}},
            "Pratique de la lecture": {
                "Appétence": {},
                "Bibliothèque": {},
                "Support": {},
                "Œuvres lues": {},
                "Motifs": {},
            },
            "Orthographe, grammaire, conjugaison": {"Niveau déclaré": {}},
        },
        "regression_model": {"r2": 0, "coefficients": []},
        "anova_multifactorial": [],
    }

    assert data == expected_empty_state


# ---------------------------------------------------------
# TEST DE SÉCURITÉ (401 UNAUTHORIZED).
# ---------------------------------------------------------
def test_get_rousseau_stats_unauthenticated(client):
    """
    Vérifie qu'un utilisateur non connecté (sans token valide) se fait rejeter par l'API avec une erreur 401.
    """
    # ACT.
    response = client.get("/api/stats/rousseau")

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


# ---------------------------------------------------------
# TEST DE GESTION D'ERREUR (500 INTERNAL SERVER ERROR).
# ---------------------------------------------------------
def test_get_rousseau_stats_internal_server_error(auth_client):
    """
    Simule un crash du service de calcul pour vérifier que l'API intercepte l'erreur (try...except) et renvoie bien une erreur 500 propre.
    """

    # ARRANGE.
    class BuggyStatsService:
        def get_rousseau_dashboard_stats(self):
            raise ValueError("Erreur mathématique imprévue générée pour le test.")

    app.dependency_overrides[get_stats_service] = lambda: BuggyStatsService()

    # ACT.
    response = auth_client.get("/api/stats/rousseau")

    # ASSERT.
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {
        "detail": "Impossible de récupérer les statistiques de l'étude Rousseau."
    }

    # CLEAN.
    app.dependency_overrides.clear()


# ---------------------------------------------------------
# TEST DE BASE (200 OK).
# ---------------------------------------------------------
def test_get_emile_stats_empty_db(auth_client):
    """
    Vérifie que l'endpoint ÉMILE renvoie un 200 OK et une structure JSON valide (avec des valeurs à 0 ou vides) quand il n'y a aucun étudiant ni dictée.
    """

    # ACT.
    response = auth_client.get("/api/stats/emile")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK, (
        f"Erreur de l'API: {response.text}"
    )

    data = response.json()

    expected_empty_state = {
        "total_students": 0,
        "total_submissions": 0,
        "global_average": 0.0,
        "group_distribution_by_promo": {},
        "group_averages": {},
        "promo_averages": {},
        "comparison_tool": {
            "Projet Voltaire (G2)": {"Initial": 0.0, "Final": 0.0},
            "Écri+ (G5)": {"Initial": 0.0, "Final": 0.0},
        },
        "comparison_human_robot": {
            "Remédiation Humaine (G4)": {"Initial": 0.0, "Final": 0.0},
            "Remédiation IA/Outil (G2, G3, G5)": {"Initial": 0.0, "Final": 0.0},
        },
        "comparison_motivation": {
            "Autonomie (G1)": 0.0,
            "Jalons obligatoires (G2)": 0.0,
            "Salle (G3)": 0.0,
            "Remédiation Humaine (G4)": 0.0,
        },
        "mistakes_stats": {"global": {}, "promotions": {}},
    }

    assert data == expected_empty_state


# ---------------------------------------------------------
# TEST DE SÉCURITÉ (401 UNAUTHORIZED).
# ---------------------------------------------------------
def test_get_emile_stats_unauthenticated(client):
    """
    Vérifie qu'un utilisateur non connecté (sans token valide) se fait rejeter par l'API avec une erreur 401.
    """
    # ACT.
    response = client.get("/api/stats/emile")

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


# ---------------------------------------------------------
# TEST DE GESTION D'ERREUR (500 INTERNAL SERVER ERROR).
# ---------------------------------------------------------
def test_get_emile_stats_internal_server_error(auth_client):
    """
    Simule un crash du service de calcul pour vérifier que l'API intercepte l'erreur (try...except) et renvoie bien une erreur 500 propre pour ÉMILE.
    """

    # ARRANGE.
    class BuggyStatsService:
        def get_emile_dashboard_stats(self):
            raise ValueError("Erreur inattendue dans le traitement d'ÉMILE.")

    app.dependency_overrides[get_stats_service] = lambda: BuggyStatsService()

    # ACT.
    response = auth_client.get("/api/stats/emile")

    # ASSERT.
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {
        "detail": "Impossible de récupérer les statistiques d'ÉMILE."
    }

    # CLEAN.
    app.dependency_overrides.clear()


# ---------------------------------------------------------
# TEST DE COUVERTURE MAXIMALE (AVEC DONNÉES).
# ---------------------------------------------------------
def test_stats_with_populated_db(auth_client, session: Session):
    """
    Test d'intégration complet :
    ARRANGE : Remplit la base de données avec un jeu de données représentatif (> 10 étudiants pour la régression, plusieurs groupes pour l'ANOVA).
    ACT : Appelle les endpoints Rousseau et ÉMILE.
    ASSERT : Vérifie que les calculs mathématiques ont bien été exécutés sans crasher et que les données ne sont plus vides.
    """

    # ARRANGE.
    promo_a = Promotion(name="Promo A")
    promo_b = Promotion(name="Promo B")

    groups = {name: Group(name=name) for name in ["G1", "G2", "G3", "G4", "G5"]}

    tool_v = Tool(name="PV", full_name="Voltaire")
    session.add(tool_v)
    session.commit()

    cat_grammaire = Category(lt_category_id="CAT_GRAMMAIRE", name="Grammaire")
    dictation = Dictation(
        title="Dictée Test",
        content_reference="Ceci est une dictée de test avec plusieurs mots.",
    )

    session.add_all(
        [promo_a, promo_b, cat_grammaire, dictation] + list(groups.values())
    )
    session.commit()

    students = []
    for i in range(1, 41):
        group_name = f"G{(i % 5) + 1}"

        appetence = 5 if group_name == "G1" else 1

        student = Student(
            anonymous_id=uuid.uuid4(),
            promotion=promo_a if i % 2 == 0 else promo_b,
            group=groups[group_name],
            appetence_level=appetence,
            declared_level=2,
            parent_1_csp=CSP.EXECUTIVE,
            parent_1_degree=Degree.HIGH_SCHOOL,
            reading_works="Manga; Romans" if i == 1 else None,
            motive="Plaisir; Information" if i == 1 else None,
        )
        session.add(student)
        students.append(student)

    session.commit()

    for i, student in enumerate(students):
        score_initial = 8.0

        if group_name == "G1":
            score_final = 0.0 + (i % 2)
        elif group_name == "G2":
            score_final = 8.0 - (i % 2)
        else:
            score_final = 4.0 - (i % 2)

        sub_init = Submission(
            student=student,
            dictation_id=dictation.id,
            content_student="Ceci est une dictée de test avec plusieurs mots.",
            assessment_type=AssessmentType.INITIAL,
            final_score=score_initial,
        )
        sub_final = Submission(
            student=student,
            dictation_id=dictation.id,
            content_student="Ceci est une dictée de test avec plusieurs mots.",
            assessment_type=AssessmentType.FINAL,
            final_score=score_final,
        )
        session.add_all([sub_init, sub_final])
        session.commit()

        session.add(
            AssessmentResult(
                student_id=student.id,
                assessment_type=AssessmentType.INITIAL,
                score=score_initial,
                tool_id=tool_v.id,
            )
        )
        session.add(
            AssessmentResult(
                student_id=student.id,
                assessment_type=AssessmentType.FINAL,
                score=score_final,
                tool_id=tool_v.id,
            )
        )

        mistake = Mistake(
            submission_id=sub_final.id,
            category_id=cat_grammaire.id,
            student_word="ses",
            correct_word="ces",
            position_index=10,
            length=3,
            malus_applied=1.0,
            rule_id_lt="FRENCH_RULE",
            message="Attention à la confusion entre ces et ses.",
            context="Il a pris ses affaires.",
            type_rousseau=MistakeType.AUTRE,
        )
        session.add(mistake)

    session.commit()

    # ACT.
    response_rousseau = auth_client.get("/api/stats/rousseau")
    response_emile = auth_client.get("/api/stats/emile")

    # ASSERT.
    assert response_rousseau.status_code == status.HTTP_200_OK
    data_r = response_rousseau.json()

    assert "h1_summary" in data_r
    assert len(data_r["h1_summary"]["dictation_final"]) > 0
    
    reg = data_r.get("regression_model", {})
    assert "r2" in reg
    assert isinstance(reg["coefficients"], list)

    assert "h2_stats_test" in data_r
    assert "anova" in data_r["h2_stats_test"]

    assert response_emile.status_code == status.HTTP_200_OK
    data_e = response_emile.json()

    assert data_e["total_students"] == 40
    assert data_e["total_submissions"] == 80

    assert "Promo A" in data_e["group_distribution_by_promo"]
    assert "G1" in data_e["group_averages"]
    assert data_e["group_averages"]["G1"]["Final"] >= 0

    assert "global" in data_e["mistakes_stats"]
    global_mistakes = data_e["mistakes_stats"]["global"]
    assert len(global_mistakes) > 0
    
    assert "comparison_tool" in data_e
    assert "comparison_human_robot" in data_e