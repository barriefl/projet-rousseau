import uuid

import pytest
from fastapi import status

from app.models import Group, Promotion, Student, Submission
from app.models.entities import Dictation
from app.schemas.assessment_schema import AssessmentType
from app.utils.crypto import encrypt_text


# ---------------------------------------------------------
# FIXTURES.
# ---------------------------------------------------------
@pytest.fixture
def setup_student_data(session):
    """Prépare une promo, un groupe, un étudiant et des scores."""
    promo = Promotion(name="BUT1")
    group = Group(name="G1")
    session.add(promo)
    session.add(group)
    session.flush()

    d1 = Dictation(title="D1", content_reference="Ref 1")
    d2 = Dictation(title="D2", content_reference="Ref 2")
    session.add(d1)
    session.add(d2)
    session.flush()

    student = Student(
        anonymous_id=uuid.uuid4(),
        first_name_encrypted=encrypt_text("Alice"),
        last_name_encrypted=encrypt_text("Wonderland"),
        promotion_id=promo.id,
        group_id=group.id,
        promotion=promo,
        group=group,
    )
    session.add(student)
    session.flush()

    sub_init = Submission(
        student_id=student.id,
        assessment_type=AssessmentType.INITIAL,
        final_score=10.0,
        dictation_id=d1.id,
        content_student="Le texte initial de l'élève.",
    )
    sub_final = Submission(
        student_id=student.id,
        assessment_type=AssessmentType.FINAL,
        final_score=15.0,
        dictation_id=d2.id,
        content_student="Le texte final de l'élève.",
    )
    session.add(sub_init)
    session.add(sub_final)
    session.commit()

    return promo, group, student


# ---------------------------------------------------------
# TEST RÉCUPÉRATION (GET).
# ---------------------------------------------------------
def test_get_students_success(auth_client, setup_student_data):
    """Vérifie la liste simple avec déchiffrement."""
    # ARRANGE via fixture.

    # ACT.
    response = auth_client.get("/api/students/")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert data[0]["first_name"] == "Alice"
    assert data[0]["promotion_name"] == "BUT1"


def test_get_students_with_scores_success(auth_client, setup_student_data):
    """Vérifie la liste avec scores Initial/Final."""
    # ARRANGE via fixture.

    # ACT.
    response = auth_client.get("/api/students/with-scores")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data[0]["initial_score"] == 10.0
    assert data[0]["final_score"] == 15.0


def test_get_student_by_uuid_success(auth_client, setup_student_data):
    """Vérifie la récupération d'un étudiant par son UUID."""
    # ARRANGE.
    _, _, student = setup_student_data

    # ACT.
    response = auth_client.get(f"/api/students/{student.anonymous_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["first_name"] == "Alice"


def test_get_student_by_uuid_not_found(auth_client):
    """Vérifie l'erreur 404 pour un UUID inconnu."""
    # ARRANGE.
    random_uuid = uuid.uuid4()

    # ACT.
    response = auth_client.get(f"/api/students/{random_uuid}")

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------
# TEST PROGRESSION & STATS.
# ---------------------------------------------------------
def test_get_students_progression_success(auth_client, setup_student_data):
    """Vérifie le calcul de la progression (15 - 10 = 5)."""
    # ARRANGE via fixture.

    # ACT.
    response = auth_client.get("/api/students/stats/progression")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data[0]["progress"] == 5.0


def test_progression_missing_scores(auth_client, session):
    """Couvre la branche où l'un des scores est absent (progress = None)."""
    # ARRANGE.
    s = Student(
        first_name_encrypted=encrypt_text("Bob"),
        last_name_encrypted=encrypt_text("B"),
        promotion_id=1,
    )
    session.add(s)
    session.commit()

    # ACT.
    response = auth_client.get("/api/students/stats/progression")

    # ASSERT.
    bob = next(x for x in response.json() if x["first_name"] == "Bob")
    assert bob["progress"] is None


# ---------------------------------------------------------
# TEST CRÉATION & MISE À JOUR.
# ---------------------------------------------------------
def test_create_student_success(auth_client, setup_student_data):
    """Vérifie la création avec chiffrement auto."""
    # ARRANGE.
    promo, group, _ = setup_student_data
    payload = {
        "first_name": "Charlie",
        "last_name": "Brown",
        "promotion_id": promo.id,
        "group_id": group.id,
    }

    # ACT.
    response = auth_client.post("/api/students/", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["first_name"] == "Charlie"


def test_update_student_names_success(auth_client, setup_student_data):
    """Vérifie la mise à jour des noms (déclenche le re-chiffrement)."""
    # ARRANGE.
    _, _, student = setup_student_data
    payload = {"first_name": "Alice-Updated", "last_name": "New-Name"}

    # ACT.
    response = auth_client.patch(f"/api/students/{student.anonymous_id}", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["first_name"] == "Alice-Updated"


def test_update_student_not_found(auth_client):
    """Vérifie 404 sur update."""
    # ACT.
    response = auth_client.patch(
        f"/api/students/{uuid.uuid4()}", json={"first_name": "X"}
    )
    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_student_other_fields_success(auth_client, setup_student_data, session):
    """Couvre la boucle setattr en mettant à jour des champs hors nom/prénom."""
    # ARRANGE.
    _, _, student = setup_student_data
    new_promo = Promotion(name="NOUVELLE PROMO")
    session.add(new_promo)
    session.commit()

    payload = {"promotion_id": new_promo.id, "appetence_level": "4"}

    # ACT.
    response = auth_client.patch(f"/api/students/{student.anonymous_id}", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["promotion_id"] == new_promo.id
    assert data["first_name"] == "Alice"


# ---------------------------------------------------------
# TEST SUPPRESSION.
# ---------------------------------------------------------
def test_delete_student_success(auth_client, setup_student_data):
    """Vérifie la suppression par UUID."""
    # ARRANGE.
    _, _, student = setup_student_data

    # ACT.
    response = auth_client.delete(f"/api/students/{student.anonymous_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_student_not_found(auth_client):
    """Vérifie 404 sur delete."""
    # ACT.
    response = auth_client.delete(f"/api/students/{uuid.uuid4()}")
    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------
# SÉCURITÉ.
# ---------------------------------------------------------
def test_students_unauthorized(client):
    """Vérifie la protection 401."""
    # ACT.
    response = client.get("/api/students/")

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
