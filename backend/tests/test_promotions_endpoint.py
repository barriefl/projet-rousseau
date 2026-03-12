import pytest
from fastapi import status

from app.models import Promotion


# ---------------------------------------------------------
# FIXTURES.
# ---------------------------------------------------------
@pytest.fixture
def setup_promotion(session):
    """Prépare une promotion en base de données."""
    promo = Promotion(name="BUT INFO 2025")
    session.add(promo)
    session.commit()
    session.refresh(promo)
    return promo


# ---------------------------------------------------------
# TEST RÉCUPÉRATION LISTE (GET /).
# ---------------------------------------------------------
def test_get_promotions_success(auth_client, setup_promotion):
    """Vérifie la récupération de toutes les promotions."""
    # ARRANGE.
    # Effectué par la fixture.

    # ACT.
    response = auth_client.get("/api/promotions/")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert any(p["name"] == "BUT INFO 2025" for p in data)


def test_get_promotions_unauthorized(client):
    """Vérifie la protection 401."""
    # ARRANGE.
    # Client non authentifié.

    # ACT.
    response = client.get("/api/promotions/")

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------
# TEST RÉCUPÉRATION PAR ID (GET /{id}).
# ---------------------------------------------------------
def test_get_promotion_by_id_success(auth_client, setup_promotion):
    """Vérifie la récupération d'une promotion par son ID."""
    # ARRANGE.
    promo_id = setup_promotion.id

    # ACT.
    response = auth_client.get(f"/api/promotions/{promo_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "BUT INFO 2025"


def test_get_promotion_by_id_not_found(auth_client):
    """Vérifie l'erreur 404 pour une promotion inexistante."""
    # ARRANGE.
    unknown_id = 9999

    # ACT.
    response = auth_client.get(f"/api/promotions/{unknown_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Promotion introuvable."


# ---------------------------------------------------------
# TEST CRÉATION (POST /).
# ---------------------------------------------------------
def test_create_promotion_success(auth_client):
    """Vérifie la création d'une nouvelle promotion."""
    # ARRANGE.
    payload = {"name": "BUT INFO 2026"}

    # ACT.
    response = auth_client.post("/api/promotions/", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "BUT INFO 2026"


def test_create_promotion_duplicate(auth_client, setup_promotion):
    """Vérifie l'erreur 400 si le nom de promotion existe déjà."""
    # ARRANGE.
    payload = {"name": "BUT INFO 2025"}

    # ACT.
    response = auth_client.post("/api/promotions/", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Cette promotion existe déjà."


# ---------------------------------------------------------
# TEST MISE À JOUR (PATCH /{id}).
# ---------------------------------------------------------
def test_update_promotion_success(auth_client, setup_promotion):
    """Vérifie la mise à jour d'une promotion."""
    # ARRANGE.
    promo_id = setup_promotion.id
    payload = {"name": "BUT INFO 2025-REVISE"}

    # ACT.
    response = auth_client.patch(f"/api/promotions/{promo_id}", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "BUT INFO 2025-REVISE"


def test_update_promotion_not_found(auth_client):
    """Vérifie l'erreur 404 lors de la mise à jour."""
    # ARRANGE.
    payload = {"name": "Inexistant"}

    # ACT.
    response = auth_client.patch("/api/promotions/9999", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------
# 5. TEST SUPPRESSION (DELETE /{id}).
# ---------------------------------------------------------
def test_delete_promotion_success(auth_client, setup_promotion):
    """Vérifie la suppression d'une promotion."""
    # ARRANGE.
    promo_id = setup_promotion.id

    # ACT.
    response = auth_client.delete(f"/api/promotions/{promo_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_promotion_not_found(auth_client):
    """Vérifie l'erreur 404 lors de la suppression."""
    # ARRANGE.
    # ID inexistant.

    # ACT.
    response = auth_client.delete("/api/promotions/9999")

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND
