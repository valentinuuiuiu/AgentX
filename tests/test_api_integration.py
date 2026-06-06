import httpx
import pytest
import uuid

# The base URL for the running API server
BASE_URL = "http://localhost:5002"

@pytest.fixture(scope="module")
def client():
    # Using httpx.Client for synchronous tests for simplicity
    with httpx.Client(base_url=BASE_URL) as client:
        yield client

@pytest.fixture(scope="module")
def new_user_credentials():
    # Generate a unique username for each test run to avoid conflicts
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "a_secure_password_123"
    return {"username": username, "password": password}

def test_health_check(client: httpx.Client):
    """Tests if the /health endpoint is reachable and reports a healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    # Check if the new database and other components are reported as active
    assert data["active_modules"]["database_pool"] is True
    assert data["active_modules"]["trading_agent"] is True

def test_register_user(client: httpx.Client, new_user_credentials: dict):
    """Tests the user registration endpoint."""
    response = client.post("/api/auth/register", data=new_user_credentials)
    assert response.status_code == 201  # Check for 201 Created status
    data = response.json()
    assert data["message"] == "User created successfully"
    assert data["user"]["username"] == new_user_credentials["username"]

    # Try to register the same user again, expecting a failure
    response = client.post("/api/auth/register", data=new_user_credentials)
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]

def test_login_and_get_token(client: httpx.Client, new_user_credentials: dict):
    """Tests the user login endpoint and token retrieval."""
    # First, ensure the user is registered (dependency not used to keep tests separate)
    # In a real test suite, you might use a fixture to ensure user exists.
    # For this script, we rely on the user being created in a previous test or run.
    # To make this test independent, we could register a new user here.
    # Let's assume test_register_user runs first or the user exists.

    login_payload = {
        "username": new_user_credentials["username"],
        "password": new_user_credentials["password"]
    }

    response = client.post("/api/auth/login", data=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"] == new_user_credentials["username"] # The user_id is the username in our case

    # Test with wrong password
    wrong_login_payload = {
        "username": new_user_credentials["username"],
        "password": "wrong_password"
    }
    response = client.post("/api/auth/login", data=wrong_login_payload)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

@pytest.fixture(scope="module")
def auth_headers(client: httpx.Client, new_user_credentials: dict) -> dict:
    """A fixture to provide authentication headers for protected endpoints."""
    # This fixture combines registration and login to provide a valid token.
    # This makes tests for protected endpoints independent.

    # 1. Register a unique user for this test module
    reg_response = client.post("/api/auth/register", data=new_user_credentials)
    assert reg_response.status_code == 201

    # 2. Log in to get the token
    login_payload = {
        "username": new_user_credentials["username"],
        "password": new_user_credentials["password"]
    }
    login_response = client.post("/api/auth/login", data=login_payload)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}

def test_get_trading_history_protected(client: httpx.Client, auth_headers: dict):
    """Tests accessing a protected endpoint (/api/trading/history) with a valid token."""
    response = client.get("/api/trading/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)

    # Test without token
    response = client.get("/api/trading/history")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_get_trading_positions_protected(client: httpx.Client, auth_headers: dict):
    """Tests accessing a protected endpoint (/api/trading/positions) with a valid token."""
    response = client.get("/api/trading/positions", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Test without token
    response = client.get("/api/trading/positions")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_hive_mind_state_endpoint(client: httpx.Client):
    """Tests the MCP integration endpoint."""
    # This endpoint is not protected in the current implementation
    response = client.get("/api/ai/hive_mind-state")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "mcp_hive_mind_layer"
    assert "mcp_data" in data
    assert "awareness_level" in data["mcp_data"]
