import json
import logging

from dataclasses import dataclass
from typing import Any, Optional

import httpx
import jwt

from pydantic import BaseModel


def get_default_logger() -> logging.Logger:
    """Create a default logger with standard configuration.

    Returns:
        logging.Logger: Configured logger instance with standard formatting
    """
    logger = logging.getLogger("synmetrix.auth")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class AuthResponse(BaseModel):
    """Response model for authentication operations.

    Attributes:
        jwt_token (str): JWT access token for API authentication
        refresh_token (str): Token used to refresh expired JWT tokens
        magicLink (Optional[bool]): Flag indicating if magic link authentication was used
        error (Optional[str]): Error message if authentication failed
        message (Optional[str]): Additional message from the server
        statusCode (Optional[int]): HTTP status code of the response
    """

    jwt_token: str
    refresh_token: str
    magicLink: Optional[bool] = None
    error: Optional[str] = None
    message: Optional[str] = None
    statusCode: Optional[int] = None


class AuthError(Exception):
    """Exception raised for authentication-related errors.

    Attributes:
        message (str): Human readable error description
        error (Optional[str]): Error type or code
        status_code (Optional[int]): HTTP status code if applicable
    """

    def __init__(
        self,
        message: str,
        error: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        self.message = message
        self.error = error
        self.status_code = status_code
        super().__init__(message)


@dataclass
class AuthTokens:
    """Data class for storing authentication tokens.

    Attributes:
        access_token (str): JWT access token for API authentication
        refresh_token (str): Token used to refresh expired JWT tokens
        access_token_expires_at (int): Expiration timestamp of the access token
        user_id (str): User ID associated with the access token
    """

    access_token: str
    refresh_token: str
    access_token_expires_at: int
    user_id: str
    allowed_roles: list[str]
    default_role: str


class AuthClient:
    """Client for handling authentication operations.

    This client provides methods for user authentication, token management,
    and session handling.

    Args:
        base_url (str): Base URL of the authentication service
        logger (Optional[logging.Logger]): Custom logger instance

    Attributes:
        base_url (str): Base URL of the authentication service
        _access_token (Optional[str]): Current JWT access token
        _refresh_token (Optional[str]): Current refresh token
        _logger (logging.Logger): Logger instance
    """

    def __init__(
        self,
        base_url: str,
        logger: Optional[logging.Logger] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._logger = logger or get_default_logger()
        self._logger.debug("Initialized AuthClient with base URL: %s", base_url)

    @property
    def auth_headers(self) -> dict[str, str]:
        """Get authorization headers using current access token.

        Returns:
            dict[str, str]: Headers dictionary with Authorization if token exists
        """
        if not self._access_token:
            return {}
        return {"Authorization": f"Bearer {self._access_token}"}

    @staticmethod
    def parse_access_token(access_token: str) -> dict[str, Any]:
        jwt_payload = jwt.decode(access_token, options={"verify_signature": False})
        hasura_payload = jwt_payload.get("hasura", {})
        user_id = hasura_payload.get("x-hasura-user-id")
        allowed_roles = hasura_payload.get("allowed_roles", [])
        default_role = hasura_payload.get("default_role")

        return {
            "user_id": user_id,
            "access_token_expires_at": jwt_payload["exp"],
            "allowed_roles": allowed_roles,
            "default_role": default_role,
        }

    async def _validate_response(self, response: httpx.Response) -> dict[str, Any]:
        """Validate and parse response."""
        try:
            # First try to get JSON data
            data = response.text
            self._logger.debug("Response data: %s", data)

            # For successful responses (2xx)
            if 200 <= response.status_code < 300:
                self._logger.debug(
                    "Successful response with status %d",
                    response.status_code,
                )

                if response.status_code == 204:
                    return {}

                try:
                    return json.loads(data)
                except json.JSONDecodeError as e:
                    self._logger.error("JSON decode error: %s", str(e), exc_info=True)

                    raise AuthError(
                        message=data,
                        error="invalid_response",
                        status_code=response.status_code,
                    ) from e
            else:
                self._logger.error("HTTP error response: %s", data)

                raise AuthError(
                    message=data,
                    error="http_error",
                    status_code=response.status_code,
                )

        except httpx.HTTPError as e:
            # For HTTP protocol errors
            self._logger.error("HTTP protocol error: %s", str(e), exc_info=True)
            raise e from e
        except ValueError as e:
            # For JSON decode errors
            self._logger.error("JSON decode error: %s", str(e), exc_info=True)
            raise AuthError(
                message=str(e),
                error="invalid_response",
                status_code=response.status_code,
            ) from e
        except Exception as e:
            # For any other errors
            self._logger.error("Unexpected error: %s", str(e), exc_info=True)
            raise e from e

    async def login(
        self, email: str, password: str, cookie: bool = False
    ) -> AuthTokens:
        """Authenticate user with email and password.

        Args:
            email (str): User's email address
            password (str): User's password
            cookie (bool, optional): Whether to set auth cookie. Defaults to False.

        Returns:
            AuthTokens: Access and refresh tokens

        Raises:
            AuthError: If authentication fails

        Example:
            ```python
            client = AuthClient("https://app.synmetrix.org")
            tokens = await client.login(email="user@example.com", password="your_password")
            print(f"Access token: {tokens.access_token}")
            ```
        """
        self._logger.info("Attempting login for user: %s", email)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    json={"email": email, "password": password, "cookie": cookie},
                )

                data = await self._validate_response(response)
                auth_response = AuthResponse(**data)

                if auth_response.error:
                    self._logger.error("Login error: %s", auth_response.error)
                    raise AuthError(
                        message=auth_response.message or "",
                        error=auth_response.error,
                        status_code=auth_response.statusCode,
                    )

                self._access_token = auth_response.jwt_token
                self._refresh_token = auth_response.refresh_token
                self._logger.info("Login successful for user: %s", email)

                parsed_access_token = AuthClient.parse_access_token(
                    auth_response.jwt_token
                )

                return AuthTokens(
                    access_token=auth_response.jwt_token,
                    refresh_token=auth_response.refresh_token,
                    **parsed_access_token,
                )
        except Exception as e:
            if isinstance(e, AuthError):
                raise
            self._logger.error("Login failed: %s", str(e), exc_info=True)
            raise AuthError(
                message=f"Login failed: {str(e)}",
                error="login_error",
            ) from e

    async def register(
        self, email: str, password: str, cookie: bool = False
    ) -> AuthTokens:
        """Register a new user.

        Args:
            email (str): User's email address
            password (str): User's password
            cookie (bool, optional): Whether to set auth cookie. Defaults to False.

        Returns:
            AuthTokens: Access and refresh tokens

        Raises:
            AuthError: If registration fails

        Example:
            ```python
            client = AuthClient("https://app.synmetrix.org")
            tokens = await client.register(
                email="user@example.com", password="your_password"
            )
            print(f"Access token: {tokens.access_token}")
            ```
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/register",
                json={"email": email, "password": password, "cookie": cookie},
            )

            data = await self._validate_response(response)
            auth_response = AuthResponse(**data)

            if auth_response.error:
                raise AuthError(
                    message=auth_response.message or "",
                    error=auth_response.error,
                )

            self._access_token = auth_response.jwt_token
            self._refresh_token = auth_response.refresh_token
            parsed_access_token = AuthClient.parse_access_token(auth_response.jwt_token)

            return AuthTokens(
                access_token=auth_response.jwt_token,
                refresh_token=auth_response.refresh_token,
                **parsed_access_token,
            )

    async def logout(self, all_sessions: bool = True) -> None:
        """Log out the current user.

        Args:
            all_sessions (bool, optional): Logout from all sessions. Defaults to True.

        Raises:
            AuthError: If not authenticated or logout fails

        Example:
            ```python
            client = AuthClient("https://app.synmetrix.org")
            await client.logout()
            ```
        """
        if not self._refresh_token or not self._access_token:
            raise AuthError("Not authenticated")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/logout",
                params={"refresh_token": self._refresh_token},
                headers=self.auth_headers,
                json={"all": all_sessions},
            )

            await self._validate_response(response)
            self._access_token = None
            self._refresh_token = None

    async def refresh_token(self, refresh_token: Optional[str] = None) -> AuthTokens:
        """Refresh access token using refresh token.

        Args:
            refresh_token (Optional[str], optional): Refresh token to use.
                If None, uses stored token. Defaults to None.

        Returns:
            AuthTokens: New access and refresh tokens

        Raises:
            AuthError: If refresh fails or no token available

        Example:
            ```python
            client = AuthClient("https://app.synmetrix.org")
            tokens = await client.refresh_token()
            print(f"Access token: {tokens.access_token}")
            ```
        """
        token = refresh_token or self._refresh_token
        if not token:
            raise AuthError("No refresh token available")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/auth/token/refresh",
                params={"refresh_token": token},
            )

            data = await self._validate_response(response)
            auth_response = AuthResponse(**data)

            if auth_response.error:
                raise AuthError(
                    message=auth_response.message or "",
                    error=auth_response.error,
                )

            self._access_token = auth_response.jwt_token
            self._refresh_token = auth_response.refresh_token
            parsed_access_token = AuthClient.parse_access_token(auth_response.jwt_token)

            return AuthTokens(
                access_token=auth_response.jwt_token,
                refresh_token=auth_response.refresh_token,
                **parsed_access_token,
            )

    async def change_password(self, old_password: str, new_password: str) -> None:
        """Change user password.

        Args:
            old_password (str): Current password
            new_password (str): New password

        Raises:
            AuthError: If not authenticated or password change fails

        Example:
            ```python
            client = AuthClient("https://app.synmetrix.org")
            await client.change_password(
                old_password="old_password", new_password="new_password"
            )
            ```
        """
        if not self._access_token:
            raise AuthError("Not authenticated")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/change-password",
                headers=self.auth_headers,
                json={
                    "old_password": old_password,
                    "new_password": new_password,
                },
            )

            await self._validate_response(response)

    async def send_magic_link(self, email: str) -> AuthTokens:
        """Send magic link for passwordless authentication.

        Args:
            email (str): User's email address

        Returns:
            AuthTokens: Access and refresh tokens after magic link verification

        Raises:
            AuthError: If magic link sending fails

        Example:
            ```python
            client = AuthClient("https://app.synmetrix.org")
            tokens = await client.send_magic_link(email="user@example.com")
            print(f"Access token: {tokens.access_token}")
            ```
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/register",
                json={"email": email, "cookie": False},
            )

            data = await self._validate_response(response)
            auth_response = AuthResponse(**data)

            if auth_response.error:
                raise AuthError(
                    message=auth_response.message or "",
                    error=auth_response.error,
                )

            self._access_token = auth_response.jwt_token
            self._refresh_token = auth_response.refresh_token

            parsed_access_token = AuthClient.parse_access_token(auth_response.jwt_token)

            return AuthTokens(
                access_token=auth_response.jwt_token,
                refresh_token=auth_response.refresh_token,
                **parsed_access_token,
            )
