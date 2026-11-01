"""
Pytest configuration and shared fixtures for the test suite.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initializes the database schema once for the test session."""
    init_db()


@pytest.fixture(scope="session")
def client():
    """Shared FastAPI TestClient across test modules for high performance."""
    with TestClient(app) as test_client:
        yield test_client
