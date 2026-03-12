import pytest
from fastapi import status
from app.models import Category, MistakeType

# ---------------------------------------------------------
# FIXTURES.
# ---------------------------------------------------------
@pytest.fixture
def setup_category(session):
    """Prépare une catégorie de test en base."""
    category = Category(
        name="Orthographe Lexicale",
        lt_category_id="TYPOS",
        type_rousseau=MistakeType.AUTRE,
        penalty=1.0
    )
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

# ---------------------------------------------------------
# TEST RÉCUPÉRATION LISTE (GET /).
# ---------------------------------------------------------
def test_get_categories_success(auth_client, setup_category):
    """Vérifie la récupération de toutes les catégories."""
    # ACT.
    response = auth_client.get("/api/categories/")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert data[0]["lt_category_id"] == "TYPOS"

def test_get_categories_unauthorized(client):
    """# TEST MAUVAIS MOT DE PASSE (401 UNAUTHORIZED)."""
    # ACT.
    response = client.get("/api/categories/")

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ---------------------------------------------------------
# TEST RÉCUPÉRATION PAR ID (GET /{id}).
# ---------------------------------------------------------
def test_get_category_by_id_success(auth_client, setup_category):
    """Vérifie la récupération d'une catégorie spécifique."""
    # ARRANGE.
    cat_id = setup_category.id

    # ACT.
    response = auth_client.get(f"/api/categories/{cat_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Orthographe Lexicale"

def test_get_category_by_id_not_found(auth_client):
    """Vérifie l'erreur 404 si l'ID n'existe pas."""
    # ACT.
    response = auth_client.get("/api/categories/999")

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Catégorie introuvable."

def test_get_category_by_id_unauthorized(client):
    """# TEST MAUVAIS MOT DE PASSE (401 UNAUTHORIZED)."""
    # ACT.
    response = client.get("/api/categories/1")

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ---------------------------------------------------------
# TEST MISE À JOUR (PATCH /{id}).
# ---------------------------------------------------------
def test_update_category_success(auth_client, setup_category):
    """Vérifie la mise à jour partielle d'une catégorie."""
    # ARRANGE.
    cat_id = setup_category.id
    payload = {
        "penalty": 2.5
    }

    # ACT.
    response = auth_client.patch(f"/api/categories/{cat_id}", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Orthographe Lexicale"
    assert data["penalty"] == 2.5
    assert data["lt_category_id"] == "TYPOS"

def test_update_category_not_found(auth_client):
    """Vérifie l'erreur 404 lors d'un patch sur ID inexistant."""
    # ACT.
    response = auth_client.patch("/api/categories/999", json={"penalty": 0.5})

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_category_unauthorized(client):
    """# TEST MAUVAIS MOT DE PASSE (401 UNAUTHORIZED)."""
    # ACT.
    response = client.patch("/api/categories/1", json={})

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED