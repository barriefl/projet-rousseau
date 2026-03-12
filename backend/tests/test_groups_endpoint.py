import pytest
from fastapi import status
from app.models import Group

# ---------------------------------------------------------
# FIXTURES.
# ---------------------------------------------------------
@pytest.fixture
def setup_group(session):
    """Prépare un groupe en base de données."""
    group = Group(name="INFO1")
    session.add(group)
    session.commit()
    session.refresh(group)
    return group

# ---------------------------------------------------------
# TEST RÉCUPÉRATION LISTE (GET /).
# ---------------------------------------------------------
def test_get_groups_success(auth_client, setup_group):
    """Vérifie la récupération de tous les groupes triés par nom."""
    # ARRANGE.
    # Effectué par la fixture setup_group.

    # ACT.
    response = auth_client.get("/api/groups/")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert any(g["name"] == "INFO1" for g in data)

def test_get_groups_unauthorized(client):
    """Vérifie que l'accès est protégé (401)."""
    # ARRANGE.
    # Pas de client authentifié.

    # ACT.
    response = client.get("/api/groups/")

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ---------------------------------------------------------
# TEST RÉCUPÉRATION PAR ID (GET /{id}).
# ---------------------------------------------------------
def test_get_group_by_id_success(auth_client, setup_group):
    """Vérifie la récupération d'un groupe par son ID."""
    # ARRANGE.
    group_id = setup_group.id

    # ACT.
    response = auth_client.get(f"/api/groups/{group_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "INFO1"

def test_get_group_by_id_not_found(auth_client):
    """Vérifie l'erreur 404 pour un groupe inexistant."""
    # ARRANGE.
    unknown_id = 999

    # ACT.
    response = auth_client.get(f"/api/groups/{unknown_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Groupe introuvable."

# ---------------------------------------------------------
# TEST CRÉATION (POST /).
# ---------------------------------------------------------
def test_create_group_success(auth_client):
    """Vérifie la création d'un nouveau groupe."""
    # ARRANGE.
    payload = {"name": "INFO2"}

    # ACT.
    response = auth_client.post("/api/groups/", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "INFO2"

def test_create_group_duplicate(auth_client, setup_group):
    """Vérifie l'erreur 400 si le nom de groupe existe déjà."""
    # ARRANGE.
    payload = {"name": "INFO1"}

    # ACT.
    response = auth_client.post("/api/groups/", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Ce groupe existe déjà."

# ---------------------------------------------------------
# TEST MISE À JOUR (PATCH /{id}).
# ---------------------------------------------------------
def test_update_group_success(auth_client, setup_group):
    """Vérifie la mise à jour du nom d'un groupe."""
    # ARRANGE.
    group_id = setup_group.id
    payload = {"name": "INFO1-BIS"}

    # ACT.
    response = auth_client.patch(f"/api/groups/{group_id}", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "INFO1-BIS"

def test_update_group_not_found(auth_client):
    """Vérifie l'erreur 404 lors de l'update d'un groupe inexistant."""
    # ARRANGE.
    unknown_id = 999
    payload = {"name": "N'importe quoi"}

    # ACT.
    response = auth_client.patch(f"/api/groups/{unknown_id}", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND

# ---------------------------------------------------------
# TEST SUPPRESSION (DELETE /{id}).
# ---------------------------------------------------------
def test_delete_group_success(auth_client, setup_group):
    """Vérifie la suppression d'un groupe."""
    # ARRANGE.
    group_id = setup_group.id

    # ACT.
    response = auth_client.delete(f"/api/groups/{group_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_delete_group_not_found(auth_client):
    """Vérifie l'erreur 404 lors de la suppression d'un groupe inexistant."""
    # ARRANGE.
    unknown_id = 999

    # ACT.
    response = auth_client.delete(f"/api/groups/{unknown_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND