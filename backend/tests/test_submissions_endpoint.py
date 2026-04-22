import socket
import uuid
from datetime import datetime
from unittest.mock import ANY, MagicMock, patch

import pytest
from fastapi import status

from app.models import (
    Dictation,
    Group,
    Mistake,
    MistakeType,
    Promotion,
    Student,
    Submission,
)
from app.schemas.assessment_schema import AssessmentType


# ---------------------------------------------------------
# FIXTURES.
# ---------------------------------------------------------
@pytest.fixture
def setup_sub_data(session):
    """Prépare les données de base pour les soumissions."""
    promo = Promotion(name="P1")
    group = Group(name="G1")
    session.add(promo)
    session.add(group)
    session.flush()

    student = Student(
        anonymous_id=uuid.uuid4(),
        first_name_encrypted=b"enc",
        last_name_encrypted=b"enc",
        promotion_id=promo.id,
        group_id=group.id,
    )
    dictation = Dictation(title="Test", content_reference="Ref text")
    session.add(student)
    session.add(dictation)
    session.commit()
    return student, dictation


@pytest.fixture
def setup_multi_students(session):
    """Prépare plusieurs étudiants pour les tests d'importation JSON."""
    promo = Promotion(name="P_JSON")
    group = Group(name="G_JSON")
    session.add(promo)
    session.add(group)
    session.flush()

    students = []
    for i in range(10):
        s = Student(
            anonymous_id=uuid.uuid4(),
            first_name_encrypted=b"enc",
            last_name_encrypted=b"enc",
            promotion_id=promo.id,
            group_id=group.id,
        )
        session.add(s)
        students.append(s)

    dictation = Dictation(
        title="Dictée JSON test",
        content_reference="Texte de référence pour le test JSON.",
    )
    session.add(dictation)
    session.commit()
    return students, dictation


# ---------------------------------------------------------
# TEST CRÉATION (POST /).
# ---------------------------------------------------------
def test_create_submission_success(auth_client, setup_sub_data):
    """Vérifie la création et le choix de l'URL LT (Docker branch)."""
    # ARRANGE.
    student, dictation = setup_sub_data
    payload = {
        "student_uuid": str(student.anonymous_id),
        "dictation_id": dictation.id,
        "assessment_type": AssessmentType.INITIAL.value,
        "content_student": "Texte élève",
    }

    with (
        patch(
            "app.endpoints.submissions_endpoint.socket.gethostbyname",
            return_value="1.2.3.4",
        ),
        patch("app.endpoints.submissions_endpoint.CorrectionService") as MockService,
    ):
        # ACT.
        response = auth_client.post("/api/submissions/", json=payload)

        # ASSERT.
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["content_student"] == "Texte élève"
        MockService.assert_called()


def test_create_submission_404_student(auth_client, setup_sub_data):
    """Erreur 404 si l'étudiant n'existe pas."""
    # ARRANGE.
    _, dictation = setup_sub_data
    payload = {
        "student_uuid": str(uuid.uuid4()),
        "dictation_id": dictation.id,
        "assessment_type": AssessmentType.INITIAL.value,
        "content_student": "X",
    }

    # ACT.
    response = auth_client.post("/api/submissions/", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_submission_correction_error(auth_client, setup_sub_data):
    """Erreur 500 si le service de correction crash."""
    # ARRANGE.
    student, dictation = setup_sub_data
    payload = {
        "student_uuid": str(student.anonymous_id),
        "dictation_id": dictation.id,
        "assessment_type": AssessmentType.INITIAL.value,
        "content_student": "X",
    }

    with patch("app.endpoints.submissions_endpoint.CorrectionService") as MockService:
        MockService.return_value.correct_submission.side_effect = Exception("Crash LT")

        # ACT.
        response = auth_client.post("/api/submissions/", json=payload)

        # ASSERT.
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Erreur lors de la correction" in response.json()["detail"]


def test_create_submission_dictation_not_found(auth_client, setup_sub_data):
    """Couvre l'erreur 404 si la dictée n'existe pas."""
    # ARRANGE.
    student, _ = setup_sub_data
    payload = {
        "student_uuid": str(student.anonymous_id),
        "dictation_id": 9999,
        "assessment_type": AssessmentType.INITIAL.value,
        "content_student": "Texte de test",
    }

    # ACT.
    response = auth_client.post("/api/submissions/", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Dictée introuvable."


def test_create_submission_lt_url_windows_branch(auth_client, setup_sub_data):
    """Force la branche LT Windows (host.docker.internal)."""
    # ARRANGE.
    student, dictation = setup_sub_data
    payload = {
        "student_uuid": str(student.anonymous_id),
        "dictation_id": dictation.id,
        "assessment_type": AssessmentType.INITIAL.value,
        "content_student": "Texte",
    }

    def mock_gethost(host):
        if host == "languagetool":
            raise socket.gaierror
        return "127.0.0.1"

    with (
        patch(
            "app.endpoints.submissions_endpoint.socket.gethostbyname",
            side_effect=mock_gethost,
        ),
        patch("app.endpoints.submissions_endpoint.CorrectionService") as MockService,
    ):
        # ACT.
        auth_client.post("/api/submissions/", json=payload)

        # ASSERT.
        MockService.assert_called_with(
            ANY, lt_url="http://host.docker.internal:8010/v2/check"
        )


# ---------------------------------------------------------
# TEST BULK (POST /bulk).
# ---------------------------------------------------------
def test_create_bulk_submissions_mixed(auth_client, setup_sub_data, session):
    """Teste le bulk avec : une nouvelle, une existante à mettre à jour, et un inconnu."""
    # ARRANGE.
    student, dictation = setup_sub_data

    existing = Submission(
        student_id=student.id,
        dictation_id=dictation.id,
        assessment_type=AssessmentType.INITIAL.value,
        content_student="Vieux",
        scores={},
    )
    session.add(existing)
    session.flush()
    mistake = Mistake(
        submission_id=existing.id,
        student_word="Vieux",
        correct_word="X",
        type_rousseau=MistakeType.AUTRE.value,
        position_index=0,
        length=1,
        category_id=1,
        malus_applied=1.0,
        rule_id_lt="FIDELITY",
        message="Erreur",
        context="context",
    )
    session.add(mistake)
    session.commit()

    payload = [
        {
            "student_uuid": str(student.anonymous_id),
            "dictation_id": dictation.id,
            "assessment_type": AssessmentType.INITIAL.value,
            "content_student": "Nouveau contenu",
        },
        {
            "student_uuid": str(uuid.uuid4()),
            "dictation_id": dictation.id,
            "assessment_type": AssessmentType.FINAL.value,
            "content_student": "Ignoré",
        },
    ]

    with (
        patch(
            "app.endpoints.submissions_endpoint.socket.gethostbyname",
            side_effect=socket.gaierror,
        ),
        patch("app.endpoints.submissions_endpoint.CorrectionService") as MockService,
    ):
        # ACT.
        response = auth_client.post("/api/submissions/bulk", json=payload)

        # ASSERT.
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data) == 1
        assert data[0]["content_student"] == "Nouveau contenu"
        assert MockService.called


def test_create_bulk_submissions_new_and_correction_error(
    auth_client, setup_sub_data, session
):
    """Couvre la création d'une nouvelle copie et le catch d'erreur de correction."""
    # ARRANGE.
    student, dictation = setup_sub_data

    mock_sub = MagicMock()
    mock_sub.id = 1
    mock_sub.mistakes = [MagicMock()]
    mock_sub.created_at = datetime.now()
    mock_sub.dictation_id = dictation.id
    mock_sub.content_student = "Update"
    mock_sub.assessment_type = AssessmentType.INITIAL
    mock_sub.final_score = 0.0
    mock_sub.scores = {}
    mock_sub.mistakes = []

    payload = [
        {
            "student_uuid": str(student.anonymous_id),
            "dictation_id": dictation.id,
            "assessment_type": AssessmentType.INITIAL.value,
            "content_student": "Update",
        }
    ]

    with (
        patch("app.endpoints.submissions_endpoint.hasattr", return_value=True),
        patch("sqlmodel.Session.exec") as mock_exec,
        patch("sqlmodel.Session.add"),
        patch("sqlmodel.Session.delete"),
        patch("sqlmodel.Session.refresh"),
        patch("sqlmodel.Session.commit"),
        patch("app.endpoints.submissions_endpoint.CorrectionService") as MockService,
    ):
        mock_exec.return_value.all.return_value = [student]
        mock_exec.return_value.first.return_value = mock_sub
        MockService.return_value.correct_submission.side_effect = Exception("Err")

        # ACT.
        response = auth_client.post("/api/submissions/bulk", json=payload)

        # ASSERT.
        assert response.status_code == status.HTTP_201_CREATED
        assert mock_sub.html_text is None
        assert response.json()[0]["content_student"] == "Update"


def test_create_bulk_submissions_multiple_students(
    auth_client, setup_multi_students, session
):
    """
    Simule l'importation bulk typique d'un JSON multi-étudiants.
    Vérifie que plusieurs soumissions sont créées pour des étudiants différents
    et que chacune est indépendante.
    """
    # ARRANGE.
    students, dictation = setup_multi_students

    payload = [
        {
            "student_uuid": str(s.anonymous_id),
            "dictation_id": dictation.id,
            "assessment_type": AssessmentType.INITIAL.value,
            "content_student": f"Texte de l'étudiant {i}",
        }
        for i, s in enumerate(students)
    ]

    with (
        patch(
            "app.endpoints.submissions_endpoint.socket.gethostbyname",
            side_effect=socket.gaierror,
        ),
        patch("app.endpoints.submissions_endpoint.CorrectionService") as MockService,
    ):
        MockService.return_value.correct_submission.return_value = None

        # ACT.
        response = auth_client.post("/api/submissions/bulk", json=payload)

        # ASSERT.
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data) == len(students)
        contents = [d["content_student"] for d in data]
        for i in range(len(students)):
            assert f"Texte de l'étudiant {i}" in contents


def test_create_bulk_submissions_empty_payload(auth_client, setup_sub_data):
    """Un payload vide doit retourner une liste vide sans erreur."""
    # ARRANGE.
    with (
        patch(
            "app.endpoints.submissions_endpoint.socket.gethostbyname",
            side_effect=socket.gaierror,
        ),
        patch("app.endpoints.submissions_endpoint.CorrectionService"),
    ):
        # ACT.
        response = auth_client.post("/api/submissions/bulk", json=[])

        # ASSERT.
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == []


def test_create_bulk_submissions_overwrite_existing(
    auth_client, setup_sub_data, session
):
    """
    Vérifie que la soumission existante est écrasée lors d'une réimportation
    (cas typique : réimportation d'un JSON après correction d'une faute de saisie).
    """
    # ARRANGE.
    student, dictation = setup_sub_data

    existing = Submission(
        student_id=student.id,
        dictation_id=dictation.id,
        assessment_type=AssessmentType.INITIAL.value,
        content_student="Ancien contenu",
        scores={"Grammaire": 2.0},
        final_score=2.0,
    )
    session.add(existing)
    session.commit()

    payload = [
        {
            "student_uuid": str(student.anonymous_id),
            "dictation_id": dictation.id,
            "assessment_type": AssessmentType.INITIAL.value,
            "content_student": "Contenu corrigé après réimportation JSON",
        }
    ]

    with (
        patch(
            "app.endpoints.submissions_endpoint.socket.gethostbyname",
            side_effect=socket.gaierror,
        ),
        patch("app.endpoints.submissions_endpoint.CorrectionService") as MockService,
    ):
        MockService.return_value.correct_submission.return_value = None

        # ACT.
        response = auth_client.post("/api/submissions/bulk", json=payload)

        # ASSERT.
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data) == 1
        assert data[0]["content_student"] == "Contenu corrigé après réimportation JSON"


def test_create_bulk_submissions_chunk_processing(
    auth_client, setup_multi_students, session
):
    """
    Vérifie que des gros volumes (> 5 éléments, taille d'un chunk) sont bien
    traités intégralement. Simule le comportement côté backend lors d'un
    import JSON contenant de nombreuses entrées.
    """
    # ARRANGE.
    students, dictation = setup_multi_students

    payload = [
        {
            "student_uuid": str(s.anonymous_id),
            "dictation_id": dictation.id,
            "assessment_type": AssessmentType.FINAL.value,
            "content_student": f"Réponse finale étudiant {i}",
        }
        for i, s in enumerate(students)
    ]

    with (
        patch(
            "app.endpoints.submissions_endpoint.socket.gethostbyname",
            side_effect=socket.gaierror,
        ),
        patch("app.endpoints.submissions_endpoint.CorrectionService") as MockService,
    ):
        MockService.return_value.correct_submission.return_value = None

        # ACT.
        response = auth_client.post("/api/submissions/bulk", json=payload)

        # ASSERT.
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.json()) == len(students)


# ---------------------------------------------------------
# TEST RÉCUPÉRATION (GET).
# ---------------------------------------------------------
def test_get_submissions_filtered(auth_client, setup_sub_data, session):
    """Vérifie le filtrage par student_uuid et le cas student non trouvé."""
    # ARRANGE.
    student, dictation = setup_sub_data

    sub = Submission(
        student_id=student.id,
        dictation_id=dictation.id,
        assessment_type=AssessmentType.INITIAL,
        content_student="Test",
        scores={},
    )
    session.add(sub)
    session.commit()

    # ACT.
    response = auth_client.get(f"/api/submissions/?student_uuid={student.anonymous_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert str(data[0]["student_uuid"]) == str(student.anonymous_id)


def test_get_submission_by_id_full(auth_client, setup_sub_data, session):
    """Vérifie le GET détaillé avec HTML et erreurs 404."""
    # ARRANGE.
    student, dictation = setup_sub_data
    sub = Submission(
        student_id=student.id,
        dictation_id=dictation.id,
        assessment_type=AssessmentType.INITIAL.value,
        content_student="Texte",
        scores={},
    )
    session.add(sub)
    session.commit()

    # ACT.
    resp_success = auth_client.get(f"/api/submissions/{sub.id}")
    resp_404 = auth_client.get("/api/submissions/9999")

    # ASSERT.
    assert resp_success.status_code == status.HTTP_200_OK
    assert "html_text" in resp_success.json()
    assert resp_404.status_code == status.HTTP_404_NOT_FOUND


def test_get_all_submissions_no_filter_success(auth_client, setup_sub_data, session):
    """Couvre la branche 'else' (récupération de TOUTES les soumissions)."""
    # ARRANGE
    student, dictation = setup_sub_data
    sub = Submission(
        student_id=student.id,
        dictation_id=dictation.id,
        assessment_type=AssessmentType.INITIAL,
        content_student="Test",
        scores={},
    )
    session.add(sub)
    session.commit()

    # ACT.
    response = auth_client.get("/api/submissions/")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 1


def test_get_all_submissions_student_not_found(auth_client):
    """Couvre le 'if not student: return []'."""
    # ACT.
    response = auth_client.get(f"/api/submissions/?student_uuid={uuid.uuid4()}")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
