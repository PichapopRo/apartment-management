import os
import pathlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _set_test_env():
    test_db_path = pathlib.Path(__file__).parent / "test.db"
    if test_db_path.exists():
        test_db_path.unlink()
    os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{test_db_path}"
    os.environ["SECRET_KEY"] = "test-secret"
    yield
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture()
def client():
    # Import after env is set
    from database import Base, engine
    from main import app

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as c:
        yield c
