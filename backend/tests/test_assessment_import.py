import pytest
from fastapi import status
from sqlmodel import select

from app.models import AssessmentResult, Promotion, Student, Tool
from app.schemas.assessment_schema import AssessmentExecuteRequest, AssessmentType
from app.services.assessment_import_service import AssessmentImportService
from app.utils.crypto import encrypt_text


# ---------------------------------------------------------
# FIXTURES.
# ---------------------------------------------------------
@pytest.fixture
def setup_assessment_data(session):
    """Prépare l'environnement pour les évaluations."""
    promo = Promotion(name="Promo 2026")
    session.add(promo)

    tool_pv = Tool(name="PV", full_name="Projet Voltaire")
    tool_ecri = Tool(name="E+", full_name="Ecri+")
    session.add(tool_pv)
    session.add(tool_ecri)
    session.flush()

    student = Student(
        promotion_id=promo.id,
        first_name_encrypted=encrypt_text("Jean"),
        last_name_encrypted=encrypt_text("DUPONT"),
        tool_id=tool_pv.id,
    )
    session.add(student)
    session.commit()

    return promo, student, tool_pv, tool_ecri


# ---------------------------------------------------------
# TESTS LOGIQUE VOLTAIRE (SERVICE).
# ---------------------------------------------------------
def test_analyze_voltaire_initial(session, setup_assessment_data):
    """Vérifie l'extraction des données Voltaire Initial."""
    # ARRANGE.
    promo, _, tool_pv, _ = setup_assessment_data
    service = AssessmentImportService(session)
    csv_content = (
        "Nom;Prénom;Score évaluation initiale;Temps évaluation initiale\n"
        "DUPONT;Jean;850;01:20:00"
    ).encode("utf-8")

    # ACT.
    preview = service.analyze_file(
        promo.id, tool_pv.id, AssessmentType.INITIAL, csv_content
    )

    # ASSERT.
    assert len(preview.matched_results) == 1
    assert preview.matched_results[0].score == 8.5
    assert preview.matched_results[0].details["temps_initial"] == "01:20:00"


def test_analyze_voltaire_final_with_blancs(session, setup_assessment_data):
    """Vérifie l'extraction Voltaire Final et les colonnes dynamiques 'blancs'."""
    # ARRANGE.
    promo, _, tool_pv, _ = setup_assessment_data
    service = AssessmentImportService(session)
    csv_content = (
        "Nom;Prénom;Score évaluation evaluation finale;Test blanc 1;Test blanc 2;Niveau atteint\n"
        "DUPONT;Jean;0.95;80;90;4"
    ).encode("utf-8")

    # ACT.
    preview = service.analyze_file(
        promo.id, tool_pv.id, AssessmentType.FINAL, csv_content
    )

    # ASSERT.
    assert preview.matched_results[0].score == 0.95
    assert preview.matched_results[0].details["tests_blancs"] == [0.8, 0.9]
    assert preview.matched_results[0].details["niveau_atteint"] == 4.0


# ---------------------------------------------------------
# TESTS LOGIQUE ECRI+ (SERVICE).
# ---------------------------------------------------------
def test_analyze_ecriplus_success(session, setup_assessment_data):
    """Vérifie l'extraction des domaines de compétence Ecri+."""
    # ARRANGE.
    promo, _, _, tool_ecri = setup_assessment_data
    service = AssessmentImportService(session)
    csv_content = (
        "Nom d'usage;Prénom;% maîtrise de l'ensemble;orthographe grammaticale %;ses mots et ses expressions %\n"
        "DUPONT;Jean;75,5;60;80"
    ).encode("utf-8")

    # ACT.
    preview = service.analyze_file(
        promo.id, tool_ecri.id, AssessmentType.INITIAL, csv_content
    )

    # ASSERT.
    assert preview.matched_results[0].score == 0.755
    assert preview.matched_results[0].details["score_orthographe_grammaticale"] == 0.6
    assert preview.matched_results[0].details["score_expression"] == 0.8


# ---------------------------------------------------------
# TESTS ERREURS PARSING (SERVICE).
# ---------------------------------------------------------
def test_analyze_file_errors(session):
    """Vérifie les levées d'erreurs sur fichiers corrompus."""
    service = AssessmentImportService(session)

    # ARRANGE & ACT & ASSERT.
    with pytest.raises(ValueError, match="CSV est vide"):
        service.analyze_file(1, 1, AssessmentType.INITIAL, b"")

    with pytest.raises(ValueError, match="Impossible de trouver les colonnes"):
        service.analyze_file(
            1, 1, AssessmentType.INITIAL, b"Mauvais;Header\nVal1;Val2"
        )


# ---------------------------------------------------------
# TEST EXECUTION (CREATE / UPDATE / ROLLBACK).
# ---------------------------------------------------------
def test_execute_assessment_import(session, setup_assessment_data):
    """Vérifie la création et la mise à jour en base."""
    # ARRANGE.
    promo, student, tool_pv, _ = setup_assessment_data
    service = AssessmentImportService(session)

    request = AssessmentExecuteRequest(
        promotion_id=promo.id,
        tool_id=tool_pv.id,
        assessment_type=AssessmentType.INITIAL,
        results=[{"student_id": student.id, "score": 0.5, "details": {}}],
    )

    # ACT (Create).
    res1 = service.execute_import(request)
    # ACT (Update).
    request.results[0].score = 0.9
    res2 = service.execute_import(request)

    # ASSERT.
    assert res1["created"] == 1
    assert res2["updated"] == 1
    db_res = session.exec(select(AssessmentResult)).first()
    assert db_res.score == 0.9


def test_execute_assessment_rollback(session, setup_assessment_data, monkeypatch):
    """Vérifie le rollback en cas d'erreur DB."""
    # ARRANGE.
    promo, student, tool_pv, _ = setup_assessment_data
    service = AssessmentImportService(session)
    monkeypatch.setattr(session, "commit", lambda: exec('raise Exception("DB Error")'))

    request = AssessmentExecuteRequest(
        promotion_id=promo.id,
        tool_id=tool_pv.id,
        assessment_type=AssessmentType.INITIAL,
        results=[{"student_id": student.id, "score": 0.5, "details": {}}],
    )

    # ACT & ASSERT.
    with pytest.raises(Exception):
        service.execute_import(request)


# ---------------------------------------------------------
# TESTS DE COUVERTURE SPÉCIFIQUES.
# ---------------------------------------------------------
def test_read_csv_encodings_and_edge_cases(session):
    """Couvre le décodage CP1252, les headers vides et les doublons."""
    # ARRANGE.
    service = AssessmentImportService(session)
    content_cp1252 = "Nom;Prénom\nÉlodie;Test".encode("cp1252")

    # ACT.
    rows = service._read_csv(content_cp1252)
    # ASSERT.
    assert rows[0]["Nom"] == "Élodie"

    # ACT.
    empty_rows = service._read_csv(b"\n\n")
    # ASSERT.
    assert empty_rows == []

    # ARRANGE.
    csv_doublons = "Score;Score;Prenom\n10;20;Jean".encode("utf-8")
    # ACT.
    rows_doublons = service._read_csv(csv_doublons)
    # ASSERT.
    assert "Score (copie 1)" in rows_doublons[0]


def test_analyze_file_fuzzy_and_skipping(session, setup_assessment_data):
    """Couvre le fuzzy match et le saut de lignes vides."""
    # ARRANGE.
    promo, student, tool_pv, _ = setup_assessment_data
    service = AssessmentImportService(session)

    csv_content = ("Nom;Prénom;Score évaluation initiale\n;;\nDUPONT;Jran;80").encode(
        "utf-8"
    )

    # ACT.
    preview = service.analyze_file(
        promo.id, tool_pv.id, AssessmentType.INITIAL, csv_content
    )

    # ASSERT.
    assert len(preview.matched_results) == 1
    assert preview.matched_results[0].match_type == "fuzzy"


def test_analyze_file_empty_csv_error(session):
    """Couvre l'erreur si le fichier est vide après parsing."""
    # ARRANGE.
    service = AssessmentImportService(session)

    # ACT & ASSERT.
    with pytest.raises(ValueError, match="Le fichier CSV est vide"):
        service.analyze_file(
            1, 1, AssessmentType.INITIAL, b"Nom;Prenom\n"
        )


def test_analyze_file_student_not_found(session, setup_assessment_data):
    """Couvre le cas où un étudiant du CSV n'a aucun match en base de données."""
    # ARRANGE.
    promo, _, tool_pv, _ = setup_assessment_data
    service = AssessmentImportService(session)

    csv_content = ("Nom;Prénom;Score évaluation initiale\nINCONNU;Xavier;50").encode(
        "utf-8"
    )

    # ACT.
    preview = service.analyze_file(
        promo.id, tool_pv.id, AssessmentType.INITIAL, csv_content
    )

    # ASSERT.
    assert len(preview.matched_results) == 0
    assert len(preview.unmatched_results) == 1
    assert preview.unmatched_results[0].match_type == "not_found"
    assert preview.unmatched_results[0].csv_nom == "INCONNU"


# ---------------------------------------------------------
# TESTS ENDPOINT : PREVIEW (SUCCESS / 401 / 400).
# ---------------------------------------------------------
def test_endpoint_assessment_preview_success(auth_client, setup_assessment_data):
    """Vérifie le succès de la preview via API."""
    # ARRANGE.
    promo, _, tool_pv, _ = setup_assessment_data
    csv_file = (
        "eval.csv",
        b"Nom;Prenom;Score evaluation initiale\nDUPONT;Jean;80",
        "text/csv",
    )

    # ACT.
    response = auth_client.post(
        "/api/import/assessments/preview",
        data={
            "promotion_id": promo.id,
            "tool_id": tool_pv.id,
            "assessment_type": AssessmentType.INITIAL.value,
        },
        files={"file": csv_file},
    )

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK


def test_endpoint_assessment_preview_unauthorized(client):
    """# TEST MAUVAIS MOT DE PASSE (401 UNAUTHORIZED)."""
    # ACT.
    response = client.post("/api/import/assessments/preview")
    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_endpoint_assessment_preview_invalid_format(auth_client):
    """Vérifie le rejet des fichiers non-CSV (400)."""
    # ACT.
    response = auth_client.post(
        "/api/import/assessments/preview",
        data={
            "promotion_id": 1,
            "tool_id": 1,
            "assessment_type": AssessmentType.INITIAL.value,
        },
        files={"file": ("test.txt", b"txt content", "text/plain")},
    )
    # ASSERT.
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------
# TEST ENDPOINT : EXECUTE (SUCCESS / 401 / 500).
# ---------------------------------------------------------
def test_endpoint_assessment_execute_success(auth_client, setup_assessment_data):
    """Vérifie l'exécution réussie via API."""
    # ARRANGE.
    promo, student, tool_ecri, _ = setup_assessment_data
    payload = {
        "promotion_id": promo.id,
        "tool_id": tool_ecri.id,
        "assessment_type": AssessmentType.FINAL.value,
        "results": [{"student_id": student.id, "score": 0.85, "details": {}}],
    }

    # ACT.
    response = auth_client.post("/api/import/assessments/execute", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK


def test_endpoint_assessment_execute_unauthorized(client):
    """# TEST MAUVAIS MOT DE PASSE (401 UNAUTHORIZED)."""
    # ACT.
    response = client.post("/api/import/assessments/execute", json={})
    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_endpoint_assessment_execute_error(auth_client, monkeypatch):
    """Vérifie le retour 500 en cas de crash service."""
    # ARRANGE.
    monkeypatch.setattr(
        "app.services.assessment_import_service.AssessmentImportService.execute_import",
        lambda *a, **k: exec('raise Exception("Critical Failure")'),
    )

    payload = {
        "promotion_id": 1,
        "tool_id": 1,
        "assessment_type": AssessmentType.INITIAL.value,
        "results": [],
    }

    # ACT.
    response = auth_client.post("/api/import/assessments/execute", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Erreur d'enregistrement" in response.json()["detail"]


# ---------------------------------------------------------
# TESTS ENDPOINT : COUVERTURE EXCEPTIONS (400).
# ---------------------------------------------------------


def test_endpoint_assessment_preview_value_error(auth_client, setup_assessment_data):
    """
    Couvre le bloc 'except Exception' de l'endpoint preview en provoquant un ValueError (colonnes manquantes).
    """
    # ARRANGE.
    promo, _, tool_pv, _ = setup_assessment_data
    bad_csv = ("test.csv", b"ColonneA;ColonneB\nValA;ValB", "text/csv")

    # ACT.
    response = auth_client.post(
        "/api/import/assessments/preview",
        data={
            "promotion_id": promo.id,
            "tool_id": tool_pv.id,
            "assessment_type": AssessmentType.INITIAL.value,
        },
        files={"file": bad_csv},
    )

    # ASSERT.
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Impossible de trouver les colonnes" in response.json()["detail"]
