"""Tests for authentication endpoints."""

from app.services.auth_service import hash_password, verify_password, create_access_token, decode_token


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "mysecretpassword"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)


class TestJWT:
    def test_create_and_decode(self):
        token = create_access_token(data={"sub": 1, "role": "admin"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "1"  # JWT sub is always stringified
        assert payload["role"] == "admin"

    def test_invalid_token(self):
        payload = decode_token("invalid.token.here")
        assert payload is None


class TestAuthEndpoints:
    def test_register(self, client):
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "new@test.com",
            "password": "password123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["role"] == "viewer"

    def test_register_duplicate_username(self, client):
        client.post("/api/auth/register", json={
            "username": "dupuser",
            "email": "dup1@test.com",
            "password": "password123",
        })
        response = client.post("/api/auth/register", json={
            "username": "dupuser",
            "email": "dup2@test.com",
            "password": "password123",
        })
        assert response.status_code == 409

    def test_login_success(self, client, admin_user):
        """Login with the pre-created admin user."""
        response = client.post("/api/auth/login", json={
            "username": "testadmin",
            "password": "password123",
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client, admin_user):
        response = client.post("/api/auth/login", json={
            "username": "testadmin",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_get_me(self, client, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["username"] == "testadmin"

    def test_get_me_unauthorized(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code in (401, 403)  # No token - HTTPBearer returns 403
