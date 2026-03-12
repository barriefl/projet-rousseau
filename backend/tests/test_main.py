from fastapi import status
from fastapi.testclient import TestClient

import app.main
from app.main import app


# ---------------------------------------------------------
# TEST ROOT ENDPOINT (/).
# ---------------------------------------------------------
def test_read_root():
    """Vérifie que la racine répond correctement (Public)."""
    # ARRANGE.
    client = TestClient(app)

    # ACT.
    response = client.get("/")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Welcome to the Projet Rousseau API!"}


# ---------------------------------------------------------
# TEST HEALTH CHECK (/health).
# ---------------------------------------------------------
def test_health_check():
    """Vérifie l'état de santé de l'API (Public)."""
    # ARRANGE.
    client = TestClient(app)

    # ACT.
    response = client.get("/health")

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}


# ---------------------------------------------------------
# TEST LIFESPAN (Startup/Shutdown).
# ---------------------------------------------------------
def test_lifespan_execution(monkeypatch):
    """Vérifie que le lifespan initialise bien la base de données."""
    # ARRANGE.
    init_called = False

    def mock_init_db():
        nonlocal init_called
        init_called = True

    monkeypatch.setattr("app.main.init_db", mock_init_db)
    monkeypatch.setattr("builtins.print", lambda *args: None)

    # ACT.
    with TestClient(app) as client:
        client.get("/health")

    # ASSERT.
    assert init_called is True
