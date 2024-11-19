import logging

from dataclasses import dataclass
from typing import Any, Optional

import httpx

from pydantic import BaseModel


def get_default_logger() -> logging.Logger:
    """Create a default logger with standard configuration."""
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
    jwt_token: str
    refresh_token: str
    magicLink: Optional[bool] = None
    error: Optional[str] = None
    message: Optional[str] = None
    statusCode: Optional[int] = None


class AuthError(Exception):
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
    access_token: str
    refresh_token: str


class AuthClient:
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
        if not self._access_token:
            return {}
        return {"Authorization": f"Bearer {self._access_token}"}

    async def _validate_response(self, response: httpx.Response) -> dict[str, Any]:
        """Validate and parse response."""
        try:
            # First try to get JSON data
            data = response.json()
            self._logger.debug("Response data: %s", data)

            # If response has error field, raise it directly
            if "error" in data:
                self._logger.error("Error in response: %s", data)
                raise AuthError(
                    message=data.get("message", ""),
                    error=data["error"],
                    status_code=response.status_code,
                )

            # For successful responses (2xx)
            if 200 <= response.status_code < 300:
                self._logger.debug(
                    "Successful response with status %d",
                    response.status_code,
                )
                return data

            # For error responses with JSON body
            self._logger.error("HTTP error response: %s", data)
            raise AuthError(
                message=data.get("message", str(response.status_code)),
                error=data.get("error", "http_error"),
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
        """Login user and return tokens."""
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

                return AuthTokens(
                    access_token=auth_response.jwt_token,
                    refresh_token=auth_response.refresh_token,
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
        """Register new user."""
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

            return AuthTokens(
                access_token=auth_response.jwt_token,
                refresh_token=auth_response.refresh_token,
            )

    async def logout(self, all_sessions: bool = True) -> None:
        """Logout user."""
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
        """Refresh access token using refresh token."""
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

            return AuthTokens(
                access_token=auth_response.jwt_token,
                refresh_token=auth_response.refresh_token,
            )

    async def change_password(self, old_password: str, new_password: str) -> None:
        """Change user password."""
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
        """Send magic link for passwordless authentication."""
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

            return AuthTokens(
                access_token=auth_response.jwt_token,
                refresh_token=auth_response.refresh_token,
            )
