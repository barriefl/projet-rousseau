import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.utils.auth import verify_token

sqlite_url = "sqlite:///:memory:"
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="engine", scope="session")
def engine_fixture():
    test_db_url = "sqlite:///:memory:"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})

    SQLModel.metadata.create_all(engine)

    yield engine

    engine.dispose()


@pytest.fixture(name="session")
def session_fixture():
    """Donne une session propre pour chaque fonction de test."""

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
        session.rollback()

    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Client normal (NON authentifié) - Idéal pour tester les erreurs 401."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


@pytest.fixture(name="auth_client")
def auth_client_fixture(session: Session):
    """Client avec un passe-droit (Authentifié) - Idéal pour tester la logique métier."""

    def get_session_override():
        return session

    def get_current_user_override():
        return {"username": "TestRousseau", "password": "MyPassword"}

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[verify_token] = get_current_user_override

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True, scope="session")
def cleanup_database_connections():
    """
    Cette fixture s'exécute automatiquement.
    À la fin de tous les tests, elle ferme proprement les connexions.
    """
    yield
    engine.dispose()
