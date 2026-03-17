import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app
from app.models import Tool


# ---------------------------------------------------------
# CONFIGURATION DU CLIENT DE TEST.
# ---------------------------------------------------------
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------
# TEST RÉCUPÉRATION LISTE (GET /).
# ---------------------------------------------------------
def test_get_tools(auth_client: TestClient, session: Session):
    """Vérifie la récupération de tous les outils disponibles."""
    # ARRANGE.
    tool_1 = Tool(name="PV", full_name="Projet Voltaire")
    tool_2 = Tool(name="E+", full_name="Ecri+")
    session.add(tool_1)
    session.add(tool_2)
    session.commit()

    # ACT.
    response = auth_client.get("/api/tools/")
    data = response.json()

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 2
    assert data[0]["name"] == "PV"
    assert data[1]["name"] == "E+"


# ---------------------------------------------------------
# TEST RÉCUPÉRATION UNITAIRE (GET /{id}).
# ---------------------------------------------------------
def test_get_tool_success(auth_client: TestClient, session: Session):
    """Vérifie la récupération d'un outil spécifique par son ID."""
    # ARRANGE.
    db_tool = Tool(name="Test Tool", full_name="Test Full Name")
    session.add(db_tool)
    session.commit()
    session.refresh(db_tool)

    # ACT.
    response = auth_client.get(f"/api/tools/{db_tool.id}")
    data = response.json()

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert data["name"] == "Test Tool"
    assert data["id"] == db_tool.id


def test_get_tool_not_found(auth_client: TestClient):
    """Vérifie l'erreur 404 si l'outil n'existe pas."""
    # ACT.
    response = auth_client.get("/api/tools/999")

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Outil non trouvé."


# ---------------------------------------------------------
# TEST CRÉATION (POST /).
# ---------------------------------------------------------
def test_create_tool_success(auth_client: TestClient):
    """Vérifie la création d'un nouvel outil."""
    # ARRANGE.
    tool_data = {"name": "Nouveau Outil", "full_name": "Test"}

    # ACT.
    response = auth_client.post("/api/tools/", json=tool_data)
    data = response.json()

    # ASSERT.
    assert response.status_code == status.HTTP_201_CREATED
    assert data["name"] == "Nouveau Outil"
    assert "id" in data


def test_create_tool_already_exists(auth_client: TestClient, session: Session):
    """Vérifie l'impossibilité de créer un doublon par nom."""
    # ARRANGE.
    existing_tool = Tool(name="Double", full_name="Double Full")
    session.add(existing_tool)
    session.commit()

    # ACT.
    response = auth_client.post(
        "/api/tools/", json={"name": "Double", "full_name": "Autre"}
    )

    # ASSERT.
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Cet outil existe déjà."


# ---------------------------------------------------------
# TEST MISE À JOUR (PATCH /{id})
# ---------------------------------------------------------
def test_update_tool_partial(auth_client: TestClient, session: Session):
    """Vérifie la mise à jour partielle d'un outil."""
    # ARRANGE.
    db_tool = Tool(name="Ancien Nom", full_name="Ancien Full Nom")
    session.add(db_tool)
    session.commit()
    session.refresh(db_tool)

    # ACT.
    response = auth_client.patch(
        f"/api/tools/{db_tool.id}", json={"name": "Nouveau Nom"}
    )
    data = response.json()

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert data["name"] == "Nouveau Nom"
    assert data["full_name"] == "Ancien Full Nom"


def test_update_tool_not_found(auth_client: TestClient):
    """Vérifie l'erreur 404 lors d'une tentative de mise à jour d'un outil inexistant."""
    # ACT.
    response = auth_client.patch("/api/tools/999", json={"name": "Nouveau Nom"})

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Outil non trouvé."


# ---------------------------------------------------------
# TEST SUPPRESSION (DELETE /{id})
# ---------------------------------------------------------
def test_delete_tool(auth_client: TestClient, session: Session):
    """Vérifie la suppression d'un outil."""
    # ARRANGE.
    db_tool = Tool(name="A supprimer", full_name="A supp")
    session.add(db_tool)
    session.commit()
    session.refresh(db_tool)

    # ACT.
    response = auth_client.delete(f"/api/tools/{db_tool.id}")

    # ASSERT.
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert session.get(Tool, db_tool.id) is None


def test_delete_tool_not_found(auth_client: TestClient):
    """Vérifie l'erreur 404 lors d'une tentative de suppression d'un outil inexistant."""
    # ACT.
    response = auth_client.delete("/api/tools/999")

    # ASSERT.
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Outil non trouvé."


# ---------------------------------------------------------
# TEST SÉCURITÉ (401 UNAUTHORIZED).
# ---------------------------------------------------------
def test_tools_unauthorized(client: TestClient):
    """Vérifie qu'un client non authentifié reçoit une 401."""
    # ACT.
    response = client.get("/api/tools/")

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
