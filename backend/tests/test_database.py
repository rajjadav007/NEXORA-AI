import uuid
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.base import Base
from app.database.session import check_db_connected, get_db
from app.models.system_setting import SystemSetting
from app.models.user import User

# Test engine bound to separate test database
test_engine = create_engine(
    settings.TEST_DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all schema tables in test database and teardown when done."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provide a transactional test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_postgres_connection():
    """Verify live PostgreSQL connectivity."""
    assert check_db_connected(test_engine) is True


def test_session_creation_and_orm_operations(db_session):
    """Verify ORM insert, UUID assignment, and query retrieval."""
    setting = SystemSetting(key="app_env", value="testing")
    user = User(email="tester@nexora.ai")

    db_session.add(setting)
    db_session.add(user)
    db_session.commit()

    # Query back
    saved_setting = db_session.execute(
        select(SystemSetting).where(SystemSetting.key == "app_env")
    ).scalar_one()
    assert isinstance(saved_setting.id, uuid.UUID)
    assert saved_setting.value == "testing"
    assert saved_setting.created_at is not None

    saved_user = db_session.execute(
        select(User).where(User.email == "tester@nexora.ai")
    ).scalar_one()
    assert isinstance(saved_user.id, uuid.UUID)
    assert saved_user.email == "tester@nexora.ai"
    assert saved_user.created_at is not None


def test_unique_constraints(db_session):
    """Verify database uniqueness constraints on key and email."""
    setting1 = SystemSetting(key="unique_key", value="val1")
    setting2 = SystemSetting(key="unique_key", value="val2")

    db_session.add(setting1)
    db_session.commit()

    db_session.add(setting2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    user1 = User(email="duplicate@nexora.ai")
    user2 = User(email="duplicate@nexora.ai")

    db_session.add(user1)
    db_session.commit()

    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_database_transaction_rollback(db_session):
    """Verify rolled-back transactions do not persist."""
    test_key = "rollback_key"
    setting = SystemSetting(key=test_key, value="will_abort")
    db_session.add(setting)
    db_session.flush()

    # Explicit rollback
    db_session.rollback()

    result = db_session.execute(
        select(SystemSetting).where(SystemSetting.key == test_key)
    ).scalar_one_or_none()
    assert result is None


def test_database_dependency():
    """Verify FastAPI get_db dependency yields active session and closes."""
    gen = get_db()
    session = next(gen)
    assert session.is_active is True
    # Ping
    result = session.execute(text("SELECT 1")).scalar()
    assert result == 1
    # Exhaust generator to trigger close
    with pytest.raises(StopIteration):
        next(gen)


def test_connection_failure_handling():
    """Verify connection failure returns False gracefully when host/port unreachable."""
    bad_engine = create_engine(
        "postgresql+psycopg2://postgres:postgres@localhost:59999/non_existent_db",
        connect_args={"connect_timeout": 1},
    )
    assert check_db_connected(bad_engine) is False
