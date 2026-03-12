from unittest.mock import patch

import pytest
from fastapi import status

from app.models import Dictation


# ---------------------------------------------------------
# FIXTURES.
# ---------------------------------------------------------
@pytest.fixture
def setup_dictation(session):
    """Crée une dictée de base en base de données."""
    dictation = Dictation(
        title="Dictée de Test", content_reference="Le petit chat dort."
    )
    session.add(dictation)
    session.commit()
    session.refresh(dictation)
    return dictation


# ---------------------------------------------------------
# TEST CRÉATION (POST /).
# ---------------------------------------------------------
def test_create_dictation_success(auth_client):
    """Vérifie la création réussie d'une dictée."""
    # ARRANGE.
    payload = {
        "title": "Nouvelle Dictée",
        "content_reference": "Ceci est un texte de référence.",
    }

    # ACT.
    response = auth_client.post("/api/dictations/", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["title"] == "Nouvelle Dictée"


def test_create_dictation_empty_content(auth_client):
    """Vérifie l'erreur 400 si le contenu est vide ou composé d'espaces."""
    # ARRANGE.
    payload = {"title": "Titre", "content_reference": "   "}

    # ACT.
    response = auth_client.post("/api/dictations/", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Le texte de la dictée ne peut pas être vide."


def test_create_dictation_unauthorized(client):
    """# TEST MAUVAIS MOT DE PASSE (401 UNAUTHORIZED)."""
    # ARRANGE.
    payload = {"title": "A", "content_reference": "B"}

    # ACT.
    response = client.post("/api/dictations/", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------
# TEST RÉCUPÉRATION LISTE (GET /).
# ---------------------------------------------------------
def test_get_dictations_success(auth_client, setup_dictation):
    """Vérifie la récupération de la liste des dictées."""
    # ARRANGE.
    # Effectué par la fixture setup_dictation.

    # ACT.
    response = auth_client.get("/api/dictations/")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert any(d["title"] == "Dictée de Test" for d in data)


# ---------------------------------------------------------
# TEST RÉCUPÉRATION PAR ID (GET /{id}).
# ---------------------------------------------------------
def test_get_dictation_by_id_success(auth_client, setup_dictation):
    """Vérifie la récupération d'une dictée par son ID."""
    # ARRANGE.
    dict_id = setup_dictation.id

    # ACT.
    response = auth_client.get(f"/api/dictations/{dict_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "Dictée de Test"


def test_get_dictation_by_id_not_found(auth_client):
    """Vérifie l'erreur 404 pour une dictée inexistante."""
    # ARRANGE.
    unknown_id = 9999

    # ACT.
    response = auth_client.get(f"/api/dictations/{unknown_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Dictée introuvable."


# ---------------------------------------------------------
# TEST RECALCUL (POST /recalculate).
# ---------------------------------------------------------
def test_recalculate_all_dictations_success(auth_client, setup_dictation):
    """Vérifie l'appel au service de recalcul pour toutes les dictées."""
    # ARRANGE.
    with patch("app.endpoints.dictations_endpoint.CorrectionService") as MockService:
        mock_instance = MockService.return_value

        # ACT.
        response = auth_client.post("/api/dictations/recalculate")

        # ASSERT.
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["detail"] == "Toutes les copies ont été recalculées."
        assert mock_instance.recalculate_dictation_scores.called
