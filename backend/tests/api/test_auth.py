"""
Integration tests for Auth API endpoints

Tests authentication and authorization functionality:
- POST /auth/register - User registration
- POST /auth/login - User login (JSON)
- POST /auth/login/oauth2 - User login (OAuth2 form)
- POST /auth/refresh - Token refresh
- GET /auth/me - Get current user info
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from core.security import verify_password, decode_token


class TestRegister:
    """Test POST /auth/register endpoint"""

    @pytest.mark.asyncio
    async def test_register_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test successful user registration"""
        registration_data = {
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "full_name": "New User",
        }

        response = await client.post(
            "/api/v1/auth/register",
            json=registration_data,
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

        # Verify user data
        user = data["user"]
        assert user["email"] == registration_data["email"]
        assert user["full_name"] == registration_data["full_name"]
        assert user["is_active"] is True
        assert "id" in user
        assert "created_at" in user
        assert "password" not in user  # Password should not be in response

        # Verify user was created in database
        result = await db_session.execute(
            select(User).where(User.email == registration_data["email"])
        )
        db_user = result.scalar_one_or_none()
        assert db_user is not None
        assert db_user.email == registration_data["email"]
        assert db_user.full_name == registration_data["full_name"]
        assert verify_password(registration_data["password"], db_user.password_hash)

        # Verify tokens are valid
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

        # Verify access token payload
        access_payload = decode_token(data["access_token"])
        assert access_payload is not None
        assert access_payload["sub"] == registration_data["email"]
        assert access_payload["type"] == "access"

        # Verify refresh token payload
        refresh_payload = decode_token(data["refresh_token"])
        assert refresh_payload is not None
        assert refresh_payload["sub"] == registration_data["email"]
        assert refresh_payload["type"] == "refresh"

    @pytest.mark.asyncio
    async def test_register_minimal_data(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test registration with minimal data (no full_name)"""
        registration_data = {
            "email": "minimal@example.com",
            "password": "StrongPassword123!",
        }

        response = await client.post(
            "/api/v1/auth/register",
            json=registration_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == registration_data["email"]
        assert data["user"]["full_name"] is None

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test registration with already registered email"""
        registration_data = {
            "email": test_user.email,  # Email already exists
            "password": "NewPassword123!",
            "full_name": "Duplicate User",
        }

        response = await client.post(
            "/api/v1/auth/register",
            json=registration_data,
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email_format(
        self,
        client: AsyncClient,
    ):
        """Test registration with invalid email format"""
        registration_data = {
            "email": "not-an-email",
            "password": "StrongPassword123!",
        }

        response = await client.post(
            "/api/v1/auth/register",
            json=registration_data,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_missing_email(
        self,
        client: AsyncClient,
    ):
        """Test registration without email"""
        registration_data = {
            "password": "StrongPassword123!",
        }

        response = await client.post(
            "/api/v1/auth/register",
            json=registration_data,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_missing_password(
        self,
        client: AsyncClient,
    ):
        """Test registration without password"""
        registration_data = {
            "email": "test@example.com",
        }

        response = await client.post(
            "/api/v1/auth/register",
            json=registration_data,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_weak_password(
        self,
        client: AsyncClient,
    ):
        """Test registration with weak password"""
        registration_data = {
            "email": "test@example.com",
            "password": "weak",  # Too short
        }

        response = await client.post(
            "/api/v1/auth/register",
            json=registration_data,
        )

        assert response.status_code == 422  # Validation error


class TestLogin:
    """Test POST /auth/login endpoint"""

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test successful login with valid credentials"""
        login_data = {
            "email": "test@example.com",
            "password": "testpassword",  # From conftest.py fixture
        }

        response = await client.post(
            "/api/v1/auth/login",
            json=login_data,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

        # Verify tokens are valid
        access_payload = decode_token(data["access_token"])
        assert access_payload is not None
        assert access_payload["sub"] == login_data["email"]
        assert access_payload["type"] == "access"

        refresh_payload = decode_token(data["refresh_token"])
        assert refresh_payload is not None
        assert refresh_payload["sub"] == login_data["email"]
        assert refresh_payload["type"] == "refresh"

    @pytest.mark.asyncio
    async def test_login_invalid_password(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test login with incorrect password"""
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword",
        }

        response = await client.post(
            "/api/v1/auth/login",
            json=login_data,
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(
        self,
        client: AsyncClient,
    ):
        """Test login with non-existent email"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "somepassword",
        }

        response = await client.post(
            "/api/v1/auth/login",
            json=login_data,
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test login with inactive user account"""
        from core.security import get_password_hash

        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            password_hash=get_password_hash("testpassword"),
            is_active=False,  # Inactive
        )
        db_session.add(inactive_user)
        await db_session.flush()

        login_data = {
            "email": "inactive@example.com",
            "password": "testpassword",
        }

        response = await client.post(
            "/api/v1/auth/login",
            json=login_data,
        )

        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_missing_email(
        self,
        client: AsyncClient,
    ):
        """Test login without email"""
        login_data = {
            "password": "testpassword",
        }

        response = await client.post(
            "/api/v1/auth/login",
            json=login_data,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_missing_password(
        self,
        client: AsyncClient,
    ):
        """Test login without password"""
        login_data = {
            "email": "test@example.com",
        }

        response = await client.post(
            "/api/v1/auth/login",
            json=login_data,
        )

        assert response.status_code == 422  # Validation error


class TestLoginOAuth2:
    """Test POST /auth/login/oauth2 endpoint (for API docs)"""

    @pytest.mark.asyncio
    async def test_oauth2_login_success(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test successful OAuth2 login"""
        # OAuth2 form data (not JSON)
        form_data = {
            "username": "test@example.com",  # Note: username, not email
            "password": "testpassword",
        }

        response = await client.post(
            "/api/v1/auth/login/oauth2",
            data=form_data,  # Form data, not JSON
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data

    @pytest.mark.asyncio
    async def test_oauth2_login_invalid_credentials(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test OAuth2 login with invalid credentials"""
        form_data = {
            "username": "test@example.com",
            "password": "wrongpassword",
        }

        response = await client.post(
            "/api/v1/auth/login/oauth2",
            data=form_data,
        )

        assert response.status_code == 401


class TestRefreshToken:
    """Test POST /auth/refresh endpoint"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test successful token refresh"""
        # First login to get refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword",
            },
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]

        # Use refresh token to get new access token
        refresh_data = {
            "refresh_token": refresh_token,
        }

        response = await client.post(
            "/api/v1/auth/refresh",
            json=refresh_data,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify new tokens are returned
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data

        # Verify new access token is valid (refresh tokens may be identical in short timeframe)
        # Note: tokens generated in same second may be identical due to exp timestamp

        # Verify new tokens are valid
        new_access_payload = decode_token(data["access_token"])
        assert new_access_payload is not None
        assert new_access_payload["sub"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(
        self,
        client: AsyncClient,
    ):
        """Test refresh with invalid token"""
        refresh_data = {
            "refresh_token": "invalid.token.here",
        }

        response = await client.post(
            "/api/v1/auth/refresh",
            json=refresh_data,
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_refresh_with_access_token(
        self,
        client: AsyncClient,
        test_user_token: str,
    ):
        """Test refresh endpoint with access token instead of refresh token"""
        refresh_data = {
            "refresh_token": test_user_token,  # This is an access token
        }

        response = await client.post(
            "/api/v1/auth/refresh",
            json=refresh_data,
        )

        assert response.status_code == 401
        assert "invalid token type" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_refresh_token_missing(
        self,
        client: AsyncClient,
    ):
        """Test refresh without providing token"""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={},
        )

        assert response.status_code == 422  # Validation error


class TestGetCurrentUser:
    """Test GET /auth/me endpoint"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test getting current user info with valid token"""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify user data
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["is_active"] == test_user.is_active
        assert "created_at" in data
        assert "updated_at" in data
        assert "password" not in data  # Password should not be in response
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(
        self,
        client: AsyncClient,
    ):
        """Test getting current user without authentication"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self,
        client: AsyncClient,
    ):
        """Test getting current user with invalid token"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_malformed_header(
        self,
        client: AsyncClient,
    ):
        """Test getting current user with malformed Authorization header"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "InvalidFormat"},
        )

        assert response.status_code == 401


class TestAuthFlow:
    """Test complete authentication flow"""

    @pytest.mark.asyncio
    async def test_complete_auth_flow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test complete auth flow: register → login → refresh → get user info"""

        # Step 1: Register
        registration_data = {
            "email": "flowtest@example.com",
            "password": "FlowTest123!",
            "full_name": "Flow Test User",
        }

        register_response = await client.post(
            "/api/v1/auth/register",
            json=registration_data,
        )
        assert register_response.status_code == 201
        register_data = register_response.json()
        initial_access_token = register_data["access_token"]
        initial_refresh_token = register_data["refresh_token"]

        # Step 2: Use access token to get user info
        headers = {"Authorization": f"Bearer {initial_access_token}"}
        me_response = await client.get(
            "/api/v1/auth/me",
            headers=headers,
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == registration_data["email"]

        # Step 3: Refresh token
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": initial_refresh_token},
        )
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        new_access_token = refresh_data["access_token"]

        # Step 4: Use new access token
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        me_response_2 = await client.get(
            "/api/v1/auth/me",
            headers=new_headers,
        )
        assert me_response_2.status_code == 200
        assert me_response_2.json()["email"] == registration_data["email"]

        # Step 5: Login again
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": registration_data["email"],
                "password": registration_data["password"],
            },
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert "refresh_token" in login_data
