import datetime

import jwt
from fastapi import status

from app.utils.auth import ADMIN_PASSWORD, ALGORITHM, SECRET_KEY, create_access_token


# ---------------------------------------------------------
# TEST DE CONNEXION (200 OK).
# ---------------------------------------------------------
def test_login_success(client):
    """Test de connexion réussie avec le bon mot de passe."""
    # ARRANGE.
    payload = {"username": "test", "password": ADMIN_PASSWORD}

    # ACT.
    response = client.post("/api/auth/login", data=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


# ---------------------------------------------------------
# TEST MAUVAIS MOT DE PASSE (401 UNAUTHORIZED).
# ---------------------------------------------------------
def test_login_wrong_password(client):
    """Test de connexion avec un mauvais mot de passe (doit échouer)."""
    # ARRANGE.
    payload = {"username": "test", "password": "wrong_password"}

    # ACT.
    response = client.post("/api/auth/login", data=payload)

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Mot de passe incorrect"


# ---------------------------------------------------------
# TESTS DES UTILITAIRES JWT (auth.py).
# ---------------------------------------------------------
def test_create_access_token():
    """Vérifie que le token généré contient les bonnes infos et expire plus tard."""
    # ARRANGE.
    data = {"sub": "test_user"}

    # ACT.
    token = create_access_token(data)

    # ASSERT.
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "test_user"
    assert "exp" in payload


def test_verify_token_valid(client):
    """Vérifie qu'un token valide permet d'accéder à une route protégée."""
    # ARRANGE.
    token = create_access_token({"sub": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    # ACT.
    response = client.get("/api/stats/rousseau", headers=headers)

    # ASSERT.
    assert response.status_code == status.HTTP_200_OK


def test_verify_token_invalid_format(client):
    """Vérifie qu'un token malformé est rejeté."""
    # ARRANGE.
    headers = {"Authorization": "Bearer nimporte_quoi"}

    # ACT.
    response = client.get("/api/stats/rousseau", headers=headers)

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Non autorisé ou token expiré"


def test_verify_token_wrong_user(client):
    """Vérifie qu'un token avec un 'sub' incorrect est rejeté."""
    # ARRANGE.
    token = create_access_token({"sub": "hacker"})
    headers = {"Authorization": f"Bearer {token}"}

    # ACT.
    response = client.get("/api/stats/rousseau", headers=headers)

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Non autorisé ou token expiré"


def test_verify_token_expired(client):
    """Vérifie qu'un token expiré est rejeté."""
    # ARRANGE.
    expired_payload = {
        "sub": "admin",
        "exp": datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(seconds=1),
    }
    token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
    headers = {"Authorization": f"Bearer {token}"}

    # ACT.
    response = client.get("/api/stats/rousseau", headers=headers)

    # ASSERT.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Non autorisé ou token expiré"
