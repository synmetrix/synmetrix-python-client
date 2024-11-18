import argparse
import asyncio
import logging

from pathlib import Path
from typing import Optional

import httpx
import yaml

from pydantic import BaseModel, Field

from synmetrix_graphql_client import Client

from .utils import setup_logger


# Constants
DEFAULT_TIMEOUT = 300.0
logger = setup_logger()


class AuthResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    user: dict


class CubeModel(BaseModel):
    name: str
    version: str
    description: str | None = None
    file_path: str
    code: str


async def authenticate(base_url: str, login: str, password: str) -> AuthResponse:
    """Authenticate user and return tokens."""
    logger.info("Authenticating user...")
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            auth_response = await client.post(
                f"{base_url}/auth/login",
                json={"email": login, "password": password, "cookie": False},
            )
            auth_response.raise_for_status()
            logger.info("Authentication successful")
            return AuthResponse.model_validate(auth_response.json())
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise


async def verify_branch(client: Client, datasource_id: str, branch_id: str) -> bool:
    """Verify that branch exists for the given datasource."""
    logger.info(f"Verifying branch {branch_id} for datasource {datasource_id}")
    try:
        # Query datasource and its branches
        datasource = await client.current_data_source(id=datasource_id)

        if not datasource.datasources_by_pk:
            logger.error(f"Datasource {datasource_id} not found")
            return False

        # Get all branches for this datasource
        branches = await client.datasources(
            where={"id": {"_eq": datasource_id}, "branches": {"id": {"_eq": branch_id}}}
        )

        # Check if branch exists
        has_branch = any(
            branch.id == branch_id
            for ds in branches.datasources
            for branch in ds.branches
        )

        if not has_branch:
            logger.error(f"Branch {branch_id} not found for datasource {datasource_id}")
            return False

        logger.info("Branch verification successful")
        return True

    except Exception as e:
        logger.error(f"Branch verification failed: {str(e)}")
        return False


async def upload_cube_models(
    client: Client,
    models: list[CubeModel],
    datasource_id: str,
    branch_id: str,
) -> None:
    """Upload multiple cube models using the GraphQL client."""
    logger.info(f"Uploading {len(models)} cube models...")

    models_data = [
        {
            "name": model.name,
            "version": model.version,
            "description": model.description or "",
            "code": model.code,
            "datasource_id": datasource_id,
        }
        for model in models
    ]

    try:
        result = await client.create_version(
            object={
                "checksum": "1",  # You might want to generate a real checksum
                "branch_id": branch_id,
                "dataschemas": {"data": models_data},
            }
        )
        logger.info("Upload successful")
        logger.debug(f"Upload result: {result}")
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise


async def main(
    base_url: str,
    datasource_id: str,
    branch_id: str,
    data_models_path: str,
    login: Optional[str] = None,
    password: Optional[str] = None,
    access_token: Optional[str] = None,
):
    logger.info(f"Starting cube model upload process from {data_models_path}")
    models_path = Path(data_models_path)
    if not models_path.exists():
        msg = f"Models path not found: {data_models_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    # Get access token either from auth or direct input
    if not access_token and (login and password):
        auth_data = await authenticate(base_url, login, password)
        access_token = auth_data.access_token
    elif not access_token:
        msg = "Either access_token or login/password must be provided"
        logger.error(msg)
        raise ValueError(msg)

    # Initialize GraphQL client
    client = Client(
        url=f"{base_url}/v1/graphql",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Verify branch exists for datasource
    if not await verify_branch(client, datasource_id, branch_id):
        raise ValueError(f"Branch {branch_id} not found for datasource {datasource_id}")

    try:
        model_files = list(models_path.glob("*.yml")) + list(models_path.glob("*.yaml"))
        logger.info(f"Found {len(model_files)} YAML files")

        if not model_files:
            logger.warning("No YAML model files found")
            return

        valid_models = []
        for model_file in model_files:
            try:
                logger.info(f"Processing: {model_file.name}")
                with open(model_file) as f:
                    yaml_content = f.read()
                    yaml_data = yaml.safe_load(yaml_content)
                    if not isinstance(yaml_data, dict) or "cubes" not in yaml_data:
                        logger.warning(f"Invalid format in {model_file}")
                        continue

                    model = CubeModel(
                        name=model_file.stem,
                        version="1.0.0",
                        file_path=str(model_file),
                        code=yaml_content,
                    )
                    valid_models.append(model)
                    logger.info(f"Validated: {model_file.name}")

            except yaml.YAMLError as e:
                logger.error(f"YAML parse error {model_file}: {str(e)}")
            except Exception as e:
                logger.error(f"Error in {model_file.name}: {str(e)}")

        if valid_models:
            await upload_cube_models(client, valid_models, datasource_id, branch_id)
            logger.info(f"Uploaded {len(valid_models)} models")
        else:
            logger.warning("No valid models found")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload OLAP cube models to the server"
    )
    parser.add_argument("--base-url", required=True, help="Base URL")
    parser.add_argument("--login", help="User login email")
    parser.add_argument("--password", help="User password")
    parser.add_argument("--access-token", help="JWT access token")
    parser.add_argument("--datasource-id", required=True, help="Datasource ID")
    parser.add_argument("--branch-id", required=True, help="Branch ID")
    parser.add_argument("--data-models-path", required=True, help="Path to YAML models")
    parser.add_argument("--debug", action="store_true", help="Debug logging")

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if not (args.access_token or (args.login and args.password)):
        parser.error("Provide either --access-token or both --login and --password")

    asyncio.run(
        main(
            base_url=args.base_url,
            datasource_id=args.datasource_id,
            branch_id=args.branch_id,
            data_models_path=args.data_models_path,
            login=args.login,
            password=args.password,
            access_token=args.access_token,
        )
    )
