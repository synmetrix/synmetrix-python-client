from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
import yaml

from httpx import Response

from synmetrix_python_client.graphql_client.client import Client
from synmetrix_python_client.use_cases.upload_data_models import (
    CubeModel,
    authenticate,
    main,
    upload_cube_models,
    verify_branch,
)


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
    """Create mock HTTP response."""

    def _create_response(status_code=200, json_data=None):
        return Response(
            status_code=status_code,
            json=json_data or {},
        )

    return _create_response


@pytest.fixture
def mock_client():
    """Create a mock GraphQL client."""
    client = AsyncMock(spec=Client)

    # Mock current_data_source response with AsyncMock
    current_ds_response = MagicMock()
    current_ds_response.datasources_by_pk = {"id": "test-ds-id"}
    client.current_data_source = AsyncMock(return_value=current_ds_response)

    # Mock datasources response with AsyncMock
    ds_response = MagicMock()
    ds_response.datasources = [MagicMock(branches=[MagicMock(id="test-branch-id")])]
    client.datasources = AsyncMock(return_value=ds_response)

    # Mock create_version response with AsyncMock
    version_response = MagicMock()
    version_response.insert_versions_one = {"id": "test-version-id"}
    client.create_version = AsyncMock(return_value=version_response)

    return client


@pytest.fixture
def test_models_dir(tmp_path):
    """Create temporary directory with test YAML models."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    # Create test model files
    valid_model = {
        "cubes": {
            "test_cube": {
                "sql_table": "test_table",
                "measures": {"count": {"type": "count"}},
                "dimensions": {"id": {"sql": "id", "type": "string"}},
            }
        }
    }

    invalid_model = {"not_cubes": {}}

    # Write test files
    with open(models_dir / "valid.yml", "w") as f:
        yaml.dump(valid_model, f)
    with open(models_dir / "invalid.yml", "w") as f:
        yaml.dump(invalid_model, f)

    return models_dir


@pytest.mark.asyncio
async def test_authenticate(mock_response, mock_jwt_token):
    """Test authentication function."""
    mock_data = {
        "jwt_token": mock_jwt_token,
        "refresh_token": "test_refresh",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = mock_response(json_data=mock_data)

        tokens = await authenticate(
            base_url="https://test.com",
            login="test@example.com",
            password="password",
        )

        assert tokens.access_token == mock_jwt_token
        assert tokens.refresh_token == "test_refresh"


@pytest.mark.asyncio
async def test_verify_branch_success(mock_client):
    """Test successful branch verification."""
    result = await verify_branch(
        client=mock_client,
        datasource_id="test-ds-id",
        branch_id="test-branch-id",
    )

    assert result is True
    mock_client.current_data_source.assert_called_once_with(id="test-ds-id")
    mock_client.datasources.assert_called_once()


@pytest.mark.asyncio
async def test_verify_branch_failure(mock_client):
    """Test branch verification with invalid IDs."""
    # Mock datasource not found with AsyncMock
    response = MagicMock()
    response.datasources_by_pk = None
    mock_client.current_data_source = AsyncMock(return_value=response)

    result = await verify_branch(
        client=mock_client,
        datasource_id="invalid-ds-id",
        branch_id="test-branch-id",
    )

    assert result is False


@pytest.mark.asyncio
async def test_upload_cube_models(mock_client):
    """Test uploading cube models."""
    models = [
        CubeModel(
            name="test_model.yml",
            file_path="test.yml",
            code="cubes: {test: {measures: {count: {type: count}}}}",
        )
    ]

    await upload_cube_models(
        client=mock_client,
        models=models,
        datasource_id="test-ds-id",
        branch_id="test-branch-id",
        user_id="test-user-id",
    )

    mock_client.create_version.assert_called_once()
    call_args = mock_client.create_version.call_args[1]
    assert call_args["object"].checksum is not None
    assert call_args["object"].branch_id == "test-branch-id"
    assert len(call_args["object"].dataschemas.data) == 1


@pytest.mark.asyncio
async def test_main_success(
    mock_client, test_models_dir, mock_response, mock_jwt_token
):
    """Test successful main execution."""
    # Mock authentication response
    mock_auth_data = {
        "jwt_token": mock_jwt_token,
        "refresh_token": "test_refresh",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = mock_response(json_data=mock_auth_data)

        with patch(
            "synmetrix_python_client.use_cases.upload_data_models.Client"
        ) as mock_client_class:
            mock_client_class.return_value = mock_client

            await main(
                base_url="https://test.com",
                datasource_id="test-ds-id",
                branch_id="test-branch-id",
                data_models_path=str(test_models_dir),
                login="test@example.com",
                password="password",
            )

            mock_client.create_version.assert_called_once()


@pytest.mark.asyncio
async def test_main_invalid_path():
    """Test main with invalid path."""
    with pytest.raises(FileNotFoundError):
        await main(
            base_url="https://test.com",
            datasource_id="test-ds-id",
            branch_id="test-branch-id",
            data_models_path="/nonexistent/path",
            access_token="test_token",
        )


@pytest.mark.asyncio
async def test_main_no_auth(tmp_path):
    """Test main without authentication."""
    # Create a valid path for testing
    test_path = tmp_path / "models"
    test_path.mkdir()

    with pytest.raises(ValueError) as exc_info:
        await main(
            base_url="https://test.com",
            datasource_id="test-ds-id",
            branch_id="test-branch-id",
            data_models_path=str(test_path),
        )
    assert "Either access_token or login/password must be provided" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_main_no_valid_models(
    mock_client, test_models_dir, mock_response, mock_jwt_token
):
    """Test main with no valid models."""
    # Remove valid model, leave only invalid one
    (test_models_dir / "valid.yml").unlink()

    # Mock authentication response
    mock_auth_data = {
        "jwt_token": mock_jwt_token,
        "refresh_token": "test_refresh",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = mock_response(json_data=mock_auth_data)

        with patch(
            "synmetrix_python_client.use_cases.upload_data_models.Client"
        ) as mock_client_class:
            # Create mock client with proper branch verification
            mock_client_class.return_value = mock_client

            await main(
                base_url="https://test.com",
                datasource_id="test-ds-id",
                branch_id="test-branch-id",
                data_models_path=str(test_models_dir),
                login="test@example.com",
                password="password",
            )

            # Verify create_version was not called
            mock_client.create_version.assert_not_called()
