import asyncio
import os

import pytest

from synmetrix_python_client.auth import AuthClient, AuthError


@pytest.mark.skipif(
    not all([os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD")]),
    reason="Test credentials not provided in environment variables",
)
@pytest.mark.integration
class TestAuthIntegration:
    @pytest.fixture
    def auth_client(self, test_env):
        """Create an AuthClient instance using shared test configuration."""
        client = AuthClient(test_env["TEST_API_URL"])
        return client

    @pytest.mark.asyncio
    async def test_login_flow(self, auth_client, test_env):
        """Test the complete login flow with real credentials."""
        try:
            # Login
            tokens = await auth_client.login(
                email=test_env["TEST_EMAIL"],
                password=test_env["TEST_PASSWORD"],
            )
            assert tokens.access_token
            assert tokens.refresh_token

            # Refresh token
            new_tokens = await auth_client.refresh_token()
            assert new_tokens.access_token
            assert new_tokens.refresh_token

            if new_tokens.access_token_expires_at != tokens.access_token_expires_at:
                assert (
                    new_tokens.access_token_expires_at > tokens.access_token_expires_at
                )
                assert str(new_tokens.access_token) != str(tokens.access_token)
            else:
                assert new_tokens.access_token == tokens.access_token
        finally:
            # Cleanup
            if auth_client._access_token:
                await auth_client.logout()

    @pytest.mark.asyncio
    async def test_invalid_credentials(self, auth_client):
        """Test login with invalid credentials."""
        with pytest.raises(AuthError):
            await auth_client.login(
                email="invalid@example.com",
                password="wrongpassword",
            )

    @pytest.mark.asyncio
    async def test_token_refresh_after_login(self, auth_client, test_env):
        """Test token refresh functionality after successful login."""
        try:
            # Initial login
            tokens = await auth_client.login(
                email=test_env["TEST_EMAIL"],
                password=test_env["TEST_PASSWORD"],
            )
            original_token = tokens.access_token

            # Wait briefly to ensure token difference
            await asyncio.sleep(1)

            # Refresh token
            new_tokens = await auth_client.refresh_token()
            if new_tokens.access_token_expires_at != tokens.access_token_expires_at:
                assert (
                    new_tokens.access_token_expires_at > tokens.access_token_expires_at
                )
                assert str(new_tokens.access_token) != str(original_token)
            else:
                assert new_tokens.access_token == original_token
        finally:
            if auth_client._access_token:
                await auth_client.logout()

    @pytest.mark.asyncio
    async def test_logout_all_sessions(self, auth_client, test_env):
        """Test logging out from all sessions."""
        try:
            # Login
            await auth_client.login(
                email=test_env["TEST_EMAIL"],
                password=test_env["TEST_PASSWORD"],
            )

            # Logout from all sessions
            await auth_client.logout(all_sessions=True)

            # Verify cannot refresh token
            with pytest.raises(AuthError):
                await auth_client.refresh_token()
        finally:
            if auth_client._access_token:
                await auth_client.logout()
