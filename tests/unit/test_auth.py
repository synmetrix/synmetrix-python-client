from unittest.mock import patch

import jwt
import pytest

from httpx import Response

from synmetrix_python_client.auth import AuthClient, AuthError


@pytest.fixture
def auth_client():
    return AuthClient("https://test.example.com")


@pytest.fixture
def mock_jwt_token():
    """Create a valid JWT token for testing with Hasura claims."""
    return jwt.encode(
        {
            "sub": "test",
            "exp": 4102444800,  # January 1, 2100
            "hasura": {
                "x-hasura-user-id": "test-user-id",
                "x-hasura-default-role": "user",
                "x-hasura-allowed-roles": ["user"],
            },
        },
        "secret",
        algorithm="HS256",
    )


@pytest.fixture
def mock_response():
    def _create_response(status_code=200, json_data=None):
        response = Response(
            status_code=status_code,
            json=json_data or {},
        )
        return response

    return _create_response


@pytest.mark.asyncio
async def test_login_success(auth_client, mock_response, mock_jwt_token):
    """Test successful login."""
    mock_data = {
        "jwt_token": mock_jwt_token,
        "refresh_token": "test_refresh",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = mock_response(json_data=mock_data)

        tokens = await auth_client.login("test@example.com", "password")

        assert tokens.access_token == mock_jwt_token
        assert tokens.refresh_token == "test_refresh"
        assert auth_client._access_token == mock_jwt_token
        assert auth_client._refresh_token == "test_refresh"

        # Verify Hasura claims
        decoded = jwt.decode(mock_jwt_token, options={"verify_signature": False})
        assert "hasura" in decoded
        assert "x-hasura-user-id" in decoded["hasura"]
        assert decoded["hasura"]["x-hasura-user-id"] == "test-user-id"


@pytest.mark.asyncio
async def test_login_failure(auth_client, mock_response):
    """Test login with invalid credentials."""
    mock_data = {"error": "invalid_credentials", "message": "Invalid credentials"}

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = mock_response(status_code=401, json_data=mock_data)

        with pytest.raises(AuthError) as exc_info:
            await auth_client.login("test@example.com", "wrong_password")

        assert exc_info.value.error == "http_error"
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_register_success(auth_client, mock_response, mock_jwt_token):
    """Test successful registration."""
    mock_data = {"jwt_token": mock_jwt_token, "refresh_token": "test_refresh"}

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = mock_response(json_data=mock_data)

        tokens = await auth_client.register("test@example.com", "password")

        assert tokens.access_token == mock_jwt_token
        assert tokens.refresh_token == "test_refresh"


@pytest.mark.asyncio
async def test_refresh_token_success(auth_client, mock_response, mock_jwt_token):
    """Test successful token refresh."""
    mock_data = {"jwt_token": mock_jwt_token, "refresh_token": "new_refresh"}

    auth_client._refresh_token = "old_refresh"

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = mock_response(json_data=mock_data)

        tokens = await auth_client.refresh_token()

        assert tokens.access_token == mock_jwt_token
        assert tokens.refresh_token == "new_refresh"
        assert auth_client._access_token == mock_jwt_token
        assert auth_client._refresh_token == "new_refresh"


@pytest.mark.asyncio
async def test_logout_success(auth_client, mock_response):
    """Test successful logout."""
    auth_client._access_token = "test_token"
    auth_client._refresh_token = "test_refresh"

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = mock_response(
            json_data={"message": "Logged out successfully"}
        )

        await auth_client.logout()

        assert auth_client._access_token is None
        assert auth_client._refresh_token is None


@pytest.mark.asyncio
async def test_change_password_success(auth_client, mock_response):
    """Test successful password change."""
    auth_client._access_token = "test_token"

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = mock_response(
            json_data={"message": "Password changed successfully"}
        )

        await auth_client.change_password("old_password", "new_password")

        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_send_magic_link_success(auth_client, mock_response, mock_jwt_token):
    """Test successful magic link sending."""
    mock_data = {"jwt_token": mock_jwt_token, "refresh_token": "test_refresh"}

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = mock_response(json_data=mock_data)

        tokens = await auth_client.send_magic_link("test@example.com")

        assert tokens.access_token == mock_jwt_token
        assert tokens.refresh_token == "test_refresh"


@pytest.mark.asyncio
async def test_refresh_token_no_token(auth_client):
    """Test refresh token when no token is available."""
    with pytest.raises(AuthError) as exc_info:
        await auth_client.refresh_token()

    assert "No refresh token available" in str(exc_info.value)


@pytest.mark.asyncio
async def test_logout_not_authenticated(auth_client):
    """Test logout when not authenticated."""
    with pytest.raises(AuthError) as exc_info:
        await auth_client.logout()

    assert "Not authenticated" in str(exc_info.value)


@pytest.mark.asyncio
async def test_change_password_not_authenticated(auth_client):
    """Test change password when not authenticated."""
    with pytest.raises(AuthError) as exc_info:
        await auth_client.change_password("old", "new")

    assert "Not authenticated" in str(exc_info.value)
