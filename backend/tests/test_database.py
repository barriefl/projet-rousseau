import os

import pytest
from sqlmodel import Session, create_engine

from app.database import get_database_url, get_session, init_db


# ---------------------------------------------------------
# TEST INITIALISATION (init_db).
# ---------------------------------------------------------
def test_init_db(monkeypatch):
    """Vérifie que la création des tables ne crash pas."""
    # ARRANGE.
    test_engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr("app.database.engine", test_engine)

    # ACT & ASSERT.
    try:
        init_db()
    except Exception as e:
        pytest.fail(f"init_db() a levé une exception inattendue : {e}")


# ---------------------------------------------------------
# TEST RÉCUPÉRATION SESSION (get_session).
# ---------------------------------------------------------
def test_get_session(monkeypatch):
    """Vérifie que le générateur yield bien une session SQLModel."""
    # ARRANGE.
    test_engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr("app.database.engine", test_engine)

    # ACT.
    session_generator = get_session()
    db_session = next(session_generator)

    # ASSERT.
    assert isinstance(db_session, Session)
    db_session.close()


# ---------------------------------------------------------
# TEST DATABASE URL (get_database_url).
# ---------------------------------------------------------
def test_get_database_url_success(monkeypatch):
    """Vérifie la récupération normale de l'URL."""
    # ARRANGE.
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")

    # ACT.
    url = get_database_url()

    # ASSERT.
    assert url == "sqlite:///test.db"


def test_database_url_missing(monkeypatch):
    """Vérifie que l'absence de DATABASE_URL lève une erreur."""
    monkeypatch.setattr(os, "environ", {})

    # ACT & ASSERT.
    with pytest.raises(ValueError, match="DATABASE_URL is not set"):
        get_database_url()
