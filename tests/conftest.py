"""
Pytest configuration and shared fixtures.
"""
import sys
import os
import pytest

# Add app directory to path so tests can import app modules
_root = os.path.join(os.path.dirname(__file__), "..")
_app = os.path.join(_root, "app")
for p in (_root, _app):
    if p not in sys.path:
        sys.path.insert(0, p)

# Set test environment
os.environ.setdefault("ENV", "development")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/srp_os")

from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app():
    """Provide the FastAPI app instance (session-scoped for speed)."""
    from api.main import app as fastapi_app
    return fastapi_app


@pytest.fixture(scope="session")
def client(app):
    """Provide a test client (session-scoped for speed)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Provide auth headers from a demo login."""
    resp = client.post("/auth/login?email=admin@demo.com&password=admin123")
    token = resp.json().get("token", "demo_token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_employee():
    """Sample employee payload."""
    return {
        "employee_id": "EMP_PYTEST_001",
        "employee_name": "Pytest Employee",
        "employee_email": "pytest@company.com",
        "department": "Engineering",
        "position": "Test Engineer",
        "start_date": "2026-03-01"
    }


@pytest.fixture
def sample_candidate():
    """Sample candidate payload."""
    return {
        "candidate_id": "CAN_PYTEST_001",
        "candidate_name": "Pytest Candidate",
        "candidate_email": "candidate@example.com",
        "position_id": "POS_TEST_001",
        "resume_url": "https://example.com/pytest_resume.pdf",
        "years_experience": 5,
        "skills": ["Python", "Testing", "FastAPI"]
    }


@pytest.fixture
def sample_invoice():
    """Sample invoice payload."""
    return {
        "client_id": "CLIENT_PYTEST_001",
        "client_name": "Pytest Client Corp",
        "client_email": "billing@pytestclient.com",
        "items": [
            {"description": "Software Development", "quantity": 10, "unit_price": 150.0},
            {"description": "Testing Services", "quantity": 5, "unit_price": 100.0}
        ]
    }
