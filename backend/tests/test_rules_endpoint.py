import pytest
from fastapi import status

from app.models import Category, MistakeType, Rule


# ---------------------------------------------------------
# FIXTURES.
# ---------------------------------------------------------
@pytest.fixture
def setup_category(session):
    """Prépare une catégorie en base."""
    category = Category(
        name="Grammaire",
        lt_category_id="GRAMMAR",
        type_rousseau=MistakeType.AUTRE,
        penalty=1.0,
    )
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@pytest.fixture
def setup_rule(session, setup_category):
    """Prépare une règle classée."""
    rule = Rule(
        lt_rule_id="RULE_1",
        description="Une règle classée",
        is_active=True,
        category_id=setup_category.id,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


@pytest.fixture
def setup_unclassified_rule(session):
    """Prépare une règle non classée (category_id is None)."""
    rule = Rule(
        lt_rule_id="RULE_UNCLASSIFIED",
        description="Règle orpheline",
        is_active=True,
        category_id=None,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


# ---------------------------------------------------------
# TEST RÉCUPÉRATION (GET).
# ---------------------------------------------------------
def test_get_all_rules_success(auth_client, setup_rule):
    """Vérifie la récupération de toutes les règles."""
    # ARRANGE via fixture.

    # ACT.
    response = auth_client.get("/api/rules/")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert any(r["lt_rule_id"] == "RULE_1" for r in data)


# ---------------------------------------------------------
# TEST CRÉATION (POST).
# ---------------------------------------------------------
def test_create_rule_success(auth_client):
    """Vérifie la création manuelle d'une règle."""
    # ARRANGE.
    payload = {
        "lt_rule_id": "NEW_RULE",
        "description": "Nouvelle règle",
        "is_active": True,
    }

    # ACT.
    response = auth_client.post("/api/rules/", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["lt_rule_id"] == "NEW_RULE"


def test_create_rule_duplicate(auth_client, setup_rule):
    """Vérifie l'erreur 400 pour un doublon d'ID LT."""
    # ARRANGE.
    payload = {"lt_rule_id": "RULE_1", "description": "Doublon"}

    # ACT.
    response = auth_client.post("/api/rules/", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Cette règle existe déjà."


# ---------------------------------------------------------
# TEST MISE À JOUR (PATCH).
# ---------------------------------------------------------
def test_update_rule_full_success(auth_client, setup_rule, setup_category):
    """Vérifie la mise à jour complète des champs d'une règle."""
    # ARRANGE.
    rule_id = setup_rule.id
    payload = {
        "description": "Description modifiée",
        "is_active": False,
        "category_id": setup_category.id,
    }

    # ACT.
    response = auth_client.patch(f"/api/rules/{rule_id}", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == "Description modifiée"
    assert data["is_active"] is False
    assert data["category_id"] == setup_category.id


def test_update_rule_unclassify(auth_client, setup_rule):
    """Vérifie qu'on peut retirer une règle d'une catégorie (set to None)."""
    # ARRANGE.
    rule_id = setup_rule.id
    payload = {"category_id": None}

    # ACT.
    response = auth_client.patch(f"/api/rules/{rule_id}", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["category_id"] is None


def test_update_rule_category_not_found(auth_client, setup_rule):
    """Vérifie l'erreur 404 si la catégorie cible n'existe pas."""
    # ARRANGE.
    rule_id = setup_rule.id
    payload = {"category_id": 9999}

    # ACT.
    response = auth_client.patch(f"/api/rules/{rule_id}", json=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Catégorie introuvable."


def test_update_rule_not_found(auth_client):
    """Vérifie l'erreur 404 si la règle n'existe pas."""
    # ACT.
    response = auth_client.patch("/api/rules/9999", json={"description": "Test"})

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------
# TEST SUPPRESSION (DELETE).
# ---------------------------------------------------------
def test_delete_rule_success(auth_client, setup_rule):
    """Vérifie la suppression d'une règle."""
    # ARRANGE.
    rule_id = setup_rule.id

    # ACT.
    response = auth_client.delete(f"/api/rules/{rule_id}")

    # ASSERT.
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_rule_not_found(auth_client):
    """Vérifie l'erreur 404 lors de la suppression d'une règle inexistante."""
    # ACT.
    response = auth_client.delete("/api/rules/9999")

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------
# SÉCURITÉ.
# ---------------------------------------------------------
def test_rules_unauthorized(client):
    """Vérifie la protection 401 sur le point d'entrée principal."""
    # ACT.
    response = client.get("/api/rules/")

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
