from unittest.mock import patch

import httpx
import pytest

from synmetrix_python_client.auth import (
    AuthClient,
    AuthError,
    AuthTokens,
)


@pytest.fixture
def auth_client():
    return AuthClient("https://app.synmetrix.org")


@pytest.fixture
def mock_response():
    return {
        "jwt_token": "test.jwt.token",
        "refresh_token": "test.refresh.token",
    }


@pytest.fixture
def mock_error_response():
    return {
        "error": "test_error",
        "message": "Test error message",
    }


class MockHTTPResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPError(f"HTTP {self.status_code}")


@pytest.mark.asyncio
async def test_login_success(auth_client, mock_response):
    """Test successful login."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = (
            MockHTTPResponse(200, mock_response)
        )

        tokens = await auth_client.login(
            email="test@example.com", password="password123"
        )

        assert isinstance(tokens, AuthTokens)
        assert tokens.access_token == mock_response["jwt_token"]
        assert tokens.refresh_token == mock_response["refresh_token"]
        assert auth_client._access_token == mock_response["jwt_token"]
        assert auth_client._refresh_token == mock_response["refresh_token"]


@pytest.mark.asyncio
async def test_login_failure(auth_client, mock_error_response):
    """Test login failure."""
    with patch("httpx.AsyncClient") as mock_client:
        # Mock response with error
        mock_response = MockHTTPResponse(400, mock_error_response)
        mock_client.return_value.__aenter__.return_value.post.return_value = (
            mock_response
        )

        with pytest.raises(AuthError) as exc_info:
            await auth_client.login(email="test@example.com", password="wrong_password")

        # Verify error details
        assert exc_info.value.error == mock_error_response["error"]
        assert exc_info.value.message == mock_error_response["message"]


@pytest.mark.asyncio
async def test_register_success(auth_client, mock_response):
    """Test successful registration."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = (
            MockHTTPResponse(200, mock_response)
        )

        tokens = await auth_client.register(
            email="new@example.com", password="newpass123"
        )

        assert isinstance(tokens, AuthTokens)
        assert tokens.access_token == mock_response["jwt_token"]
        assert tokens.refresh_token == mock_response["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_token_success(auth_client, mock_response):
    """Test successful token refresh."""
    auth_client._refresh_token = "old.refresh.token"

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value = (
            MockHTTPResponse(200, mock_response)
        )

        tokens = await auth_client.refresh_token()

        assert isinstance(tokens, AuthTokens)
        assert tokens.access_token == mock_response["jwt_token"]
        assert tokens.refresh_token == mock_response["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_token_no_token(auth_client):
    """Test refresh token failure when no token available."""
    with pytest.raises(AuthError, match="No refresh token available"):
        await auth_client.refresh_token()


@pytest.mark.asyncio
async def test_logout_success(auth_client):
    """Test successful logout."""
    auth_client._access_token = "test.access.token"
    auth_client._refresh_token = "test.refresh.token"

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = (
            MockHTTPResponse(204, {})
        )

        await auth_client.logout()

        assert auth_client._access_token is None
        assert auth_client._refresh_token is None


@pytest.mark.asyncio
async def test_logout_not_authenticated(auth_client):
    """Test logout failure when not authenticated."""
    with pytest.raises(AuthError, match="Not authenticated"):
        await auth_client.logout()


@pytest.mark.asyncio
async def test_change_password_success(auth_client):
    """Test successful password change."""
    auth_client._access_token = "test.access.token"

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = (
            MockHTTPResponse(204, {})
        )

        await auth_client.change_password(
            old_password="oldpass", new_password="newpass"
        )


@pytest.mark.asyncio
async def test_change_password_not_authenticated(auth_client):
    """Test password change failure when not authenticated."""
    with pytest.raises(AuthError, match="Not authenticated"):
        await auth_client.change_password(
            old_password="oldpass", new_password="newpass"
        )


@pytest.mark.asyncio
async def test_send_magic_link_success(auth_client, mock_response):
    """Test successful magic link request."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = (
            MockHTTPResponse(200, mock_response)
        )

        tokens = await auth_client.send_magic_link(email="test@example.com")

        assert isinstance(tokens, AuthTokens)
        assert tokens.access_token == mock_response["jwt_token"]
        assert tokens.refresh_token == mock_response["refresh_token"]


@pytest.mark.asyncio
async def test_auth_headers(auth_client):
    """Test auth headers generation."""
    # Without token
    assert auth_client.auth_headers == {}

    # With token
    auth_client._access_token = "test.token"
    assert auth_client.auth_headers == {"Authorization": "Bearer test.token"}


def test_auth_error():
    """Test AuthError exception."""
    error = AuthError("Test message", "test_error")
    assert str(error) == "Test message"
    assert error.message == "Test message"
    assert error.error == "test_error"
