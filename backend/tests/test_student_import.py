import pytest
from fastapi import status
from sqlmodel import select

from app.models import Group, Promotion, Student
from app.schemas.import_schema import CsvRowData, ImportExecuteRequest
from app.services.import_service import ImportService
from app.utils.crypto import encrypt_text


# ---------------------------------------------------------
# FIXTURES DE BASE.
# ---------------------------------------------------------
@pytest.fixture
def setup_import_data(session):
    """Prépare une promotion et un groupe pour les tests."""
    promo = Promotion(name="2025 - 2026")
    session.add(promo)
    session.flush()

    group = Group(name="Groupe A")
    session.add(group)
    session.flush()

    student = Student(
        promotion_id=promo.id,
        group_id=group.id,
        first_name_encrypted=encrypt_text("Jean"),
        last_name_encrypted=encrypt_text("DUPONT"),
    )
    session.add(student)
    session.commit()
    return promo, group, student


# ---------------------------------------------------------
# TEST ANALYSE / PREVIEW (SERVICE).
# ---------------------------------------------------------
def test_analyze_import_logic(session, setup_import_data):
    """Vérifie la détection des types de match (exact, fuzzy, new)."""
    # ARRANGE.
    promo, group, student = setup_import_data
    service = ImportService(session)

    csv_content = (
        "15. nom;16. prenom;17. groupe\n"
        "DUPONT;Jean;Groupe A\n"
        "DUPONT;Jran;Groupe A\n"
        "PETIT;Alice;Nouveau Groupe\n"
    ).encode("utf-8")

    # ACT.
    preview = service.analyze_import(promo.id, csv_content)

    # ASSERT.
    assert len(preview.exact_matches) == 1
    assert len(preview.fuzzy_matches) == 1
    assert len(preview.new_students) == 1
    assert "Nouveau Groupe" in preview.groups_to_create


# ---------------------------------------------------------
# TEST PARSING ENCODAGE (SERVICE).
# ---------------------------------------------------------
def test_parse_csv_encodings(session):
    """Vérifie que le service gère l'UTF-8-SIG et le CP1252."""
    # ARRANGE.
    service = ImportService(session)
    content_cp1252 = "15. nom;16. prenom\nBéatrice;NOM".encode("cp1252")

    # ACT.
    data = service._parse_csv(content_cp1252)

    # ASSERT.
    assert data[0].first_name == "NOM"


# ---------------------------------------------------------
# TEST EXECUTION IMPORT : CRÉATION (SERVICE).
# ---------------------------------------------------------
def test_execute_import_create(session, setup_import_data):
    """Vérifie la création effective des étudiants et des groupes."""
    # ARRANGE.
    promo, _, _ = setup_import_data
    service = ImportService(session)

    request = ImportExecuteRequest(
        promotion_id=promo.id,
        create_missing_groups=True,
        students=[
            {
                "action": "create",
                "csv_data": CsvRowData(
                    first_name="Marc", last_name="Sully", group_name="Nouveau G"
                ),
            }
        ],
    )

    # ACT.
    result = service.execute_import(request)

    # ASSERT.
    assert result["created"] == 1
    st_count = len(
        session.exec(select(Student).where(Student.promotion_id == promo.id)).all()
    )
    assert st_count == 2


# ---------------------------------------------------------
# TEST EXECUTION IMPORT : MISE À JOUR (SERVICE).
# ---------------------------------------------------------
def test_execute_import_update(session, setup_import_data):
    """Vérifie la mise à jour d'un étudiant existant."""
    # ARRANGE.
    promo, _, student = setup_import_data
    service = ImportService(session)

    request = ImportExecuteRequest(
        promotion_id=promo.id,
        create_missing_groups=False,
        students=[
            {
                "action": "update",
                "db_student_id": student.id,
                "csv_data": CsvRowData(
                    first_name="Jean-Vieux",
                    last_name="DUPONT",
                    appetence_level="Haut",
                    group_name="Groupe A",
                ),
            }
        ],
    )

    # ACT.
    service.execute_import(request)
    session.refresh(student)

    # ASSERT.
    assert student.appetence_level == "Haut"


# ---------------------------------------------------------
# TEST ERREUR ET ROLLBACK (SERVICE).
# ---------------------------------------------------------
def test_execute_import_rollback(session, setup_import_data, monkeypatch):
    """Vérifie qu'une erreur annule toute la transaction."""
    # ARRANGE.
    promo, _, _ = setup_import_data
    service = ImportService(session)

    def mock_commit():
        raise Exception("Database Error")

    monkeypatch.setattr(session, "commit", mock_commit)

    request = ImportExecuteRequest(
        promotion_id=promo.id,
        students=[
            {
                "action": "create",
                "csv_data": {"first_name": "Error", "last_name": "Test"},
            }
        ],
    )

    # ACT & ASSERT.
    with pytest.raises(Exception, match="Database Error"):
        service.execute_import(request)


# ---------------------------------------------------------
# TEST ENDPOINT : PREVIEW SUCCESS (200 OK).
# ---------------------------------------------------------
def test_endpoint_preview_success(auth_client, setup_import_data):
    """Vérifie l'appel API de l'étape 1."""
    # ARRANGE.
    promo, _, _ = setup_import_data
    csv_file = ("test.csv", b"15. nom;16. prenom;17. groupe\nTEST;Test;G1", "text/csv")

    # ACT.
    response = auth_client.post(
        "/api/import/preview", data={"promotion_id": promo.id}, files={"file": csv_file}
    )

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["promotion_id"] == promo.id


# ---------------------------------------------------------
# TEST ENDPOINT : MAUVAIS FORMAT (400 BAD REQUEST).
# ---------------------------------------------------------
def test_endpoint_preview_wrong_extension(auth_client, setup_import_data):
    """Vérifie le rejet des fichiers non-CSV."""
    # ARRANGE.
    promo, _, _ = setup_import_data
    bad_file = ("test.txt", b"content", "text/plain")

    # ACT.
    response = auth_client.post(
        "/api/import/preview", data={"promotion_id": promo.id}, files={"file": bad_file}
    )

    # ASSERT.
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "format CSV" in response.json()["detail"]


# ---------------------------------------------------------
# TEST ENDPOINT : EXECUTE EXCEPTION (500 INTERNAL ERROR).
# ---------------------------------------------------------
def test_endpoint_execute_internal_error(auth_client, monkeypatch):
    """Vérifie la levée d'une 500 en cas de crash service."""
    # ARRANGE.
    monkeypatch.setattr(
        "app.services.import_service.ImportService.execute_import",
        lambda *a: exec('raise Exception("Boom")'),
    )

    # ACT.
    response = auth_client.post(
        "/api/import/execute", json={"promotion_id": 1, "students": []}
    )

    # ASSERT.
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Erreur critique" in response.json()["detail"]


# ---------------------------------------------------------
# TEST ENDPOINT : CRASH ANALYSE (400 BAD REQUEST).
# ---------------------------------------------------------
def test_endpoint_preview_analysis_crash(auth_client, setup_import_data, monkeypatch):
    """
    Force une exception dans analyze_import pour couvrir le bloc 'except Exception' de l'endpoint preview.
    """
    # ARRANGE.
    promo, _, _ = setup_import_data
    csv_file = ("test.csv", b"nom;prenom\nSTARK;Tony", "text/csv")

    def mock_analyze_crash(*args, **kwargs):
        raise Exception("Crash imprévu du moteur d'analyse")

    monkeypatch.setattr(
        "app.services.import_service.ImportService.analyze_import", mock_analyze_crash
    )

    # ACT.
    response = auth_client.post(
        "/api/import/preview", data={"promotion_id": promo.id}, files={"file": csv_file}
    )

    # ASSERT.
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Erreur lors de l'analyse du fichier" in response.json()["detail"]
    assert "Crash imprévu" in response.json()["detail"]


# ---------------------------------------------------------
# TEST ENDPOINT : EXECUTE SUCCESS (200 OK).
# ---------------------------------------------------------
def test_endpoint_execute_success(auth_client, setup_import_data):
    """
    Vérifie le cycle complet de l'étape 2 via l'API.
    C'est ce test qui va couvrir le 'return result' de l'endpoint.
    """
    # ARRANGE.
    promo, _, _ = setup_import_data

    payload = {
        "promotion_id": promo.id,
        "create_missing_groups": True,
        "students": [
            {
                "action": "create",
                "csv_data": {
                    "first_name": "Luffy",
                    "last_name": "MONKEY D.",
                    "group_name": "Mugiwara",
                },
            }
        ],
    }

    # ACT.
    response = auth_client.post("/api/import/execute", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "success"
    assert data["created"] == 1
    assert data["updated"] == 0
