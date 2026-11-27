import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
root_dir = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(root_dir))

from app.main import app
from app.core.database import Base, get_db
from app.services.auth_service import AuthService
from app.core.security import get_password_hash, verify_password, create_access_token

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        AuthService.seed_default_users(db)
    finally:
        db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_password_hashing_security():
    """Verify that bcrypt password hashing is secure, salted, and verifies correctly."""
    raw_pwd = "ClinicalSecret@2026"
    hashed = get_password_hash(raw_pwd)
    assert hashed != raw_pwd
    assert hashed.startswith("$2b$") # bcrypt header
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_auth_login_invalid_credentials():
    """Verify that incorrect credentials return 401 without exposing account details."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@neuroscreen.ai",
        "password": "WrongPassword123"
    })
    assert resp.status_code == 401
    assert "Incorrect email or password" in resp.json()["detail"]

def test_rbac_assessor_permissions():
    """Verify Assessor role can create patients and screenings, but cannot delete patients."""
    # 1. Login as Assessor
    resp_login = client.post("/api/v1/auth/login", json={
        "email": "assessor@neuroscreen.ai",
        "password": "Assessor@12345"
    })
    assert resp_login.status_code == 200
    token = resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Can create patient
    res_create = client.post("/api/v1/patients/", json={
        "age_months": 28,
        "biological_sex": "female",
        "referral_source": "Assessor Clinic"
    }, headers=headers)
    assert res_create.status_code == 201
    patient_id = res_create.json()["id"]

    # 3. Cannot delete patient (403 Forbidden)
    res_del = client.delete(f"/api/v1/patients/{patient_id}", headers=headers)
    assert res_del.status_code == 403
    assert "Insufficient privileges" in res_del.json()["detail"]

def test_rbac_researcher_read_only_restriction():
    """Verify Researcher role has read-only access and cannot create patients or execute screenings."""
    # 1. First create a patient as admin so researcher has something to read
    resp_admin = client.post("/api/v1/auth/login", json={
        "email": "admin@neuroscreen.ai",
        "password": "Admin@12345"
    })
    admin_headers = {"Authorization": f"Bearer {resp_admin.json()['access_token']}"}
    res_pat = client.post("/api/v1/patients/", json={
        "age_months": 36,
        "biological_sex": "male",
        "referral_source": "General Clinic"
    }, headers=admin_headers)
    patient_id = res_pat.json()["id"]

    # 2. Login as Researcher
    resp_res = client.post("/api/v1/auth/login", json={
        "email": "researcher@neuroscreen.ai",
        "password": "Researcher@12345"
    })
    assert resp_res.status_code == 200
    res_token = resp_res.json()["access_token"]
    res_headers = {"Authorization": f"Bearer {res_token}"}

    # 3. Researcher CAN list and view patients
    list_resp = client.get("/api/v1/patients/", headers=res_headers)
    assert list_resp.status_code == 200

    get_resp = client.get(f"/api/v1/patients/{patient_id}", headers=res_headers)
    assert get_resp.status_code == 200

    # 4. Researcher CANNOT create patient (403 Forbidden)
    create_resp = client.post("/api/v1/patients/", json={
        "age_months": 40,
        "biological_sex": "female",
        "referral_source": "Research Attempt"
    }, headers=res_headers)
    assert create_resp.status_code == 403
    assert "Insufficient privileges" in create_resp.json()["detail"]

    # 5. Researcher CANNOT execute screening (403 Forbidden)
    screen_resp = client.post("/api/v1/screenings/", json={
        "patient_id": patient_id,
        "preferred_model": "random_forest"
    }, headers=res_headers)
    assert screen_resp.status_code == 403

def test_rbac_administrator_full_access():
    """Verify Administrator role has full access including deletion."""
    resp_admin = client.post("/api/v1/auth/login", json={
        "email": "admin@neuroscreen.ai",
        "password": "Admin@12345"
    })
    headers = {"Authorization": f"Bearer {resp_admin.json()['access_token']}"}

    # Create patient
    res_create = client.post("/api/v1/patients/", json={
        "age_months": 30,
        "biological_sex": "male",
        "referral_source": "Admin Test Clinic"
    }, headers=headers)
    assert res_create.status_code == 201
    pat_id = res_create.json()["id"]

    # Delete patient
    res_del = client.delete(f"/api/v1/patients/{pat_id}", headers=headers)
    assert res_del.status_code == 204

    # Verify deleted
    res_check = client.get(f"/api/v1/patients/{pat_id}", headers=headers)
    assert res_check.status_code == 404
    assert res_check.json()["detail"] == "Patient record not found."
