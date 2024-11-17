import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import yaml
import httpx
import logging
from .utils import setup_logger

# Constants
DEFAULT_TIMEOUT = 300.0
logger = setup_logger()


class AuthResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    user: Dict[str, Any]


class CubeModel(BaseModel):
    name: str
    version: str
    description: str | None = None
    file_path: str
    code: str


async def authenticate(
    client: httpx.AsyncClient, base_url: str, login: str, password: str
) -> AuthResponse:
    """Authenticate user and return tokens."""
    logger.info("Authenticating user...")
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


async def upload_cube_models(
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    models: List[CubeModel],
    datasource_id: str,
    branch_id: str,
) -> Dict[str, Any]:
    """Upload multiple cube models in a single request."""
    logger.info(f"Uploading {len(models)} cube models...")

    headers = {
        "Authorization": f"Bearer {token}",
        "x-hasura-datasource-id": datasource_id,
        "x-hasura-branch-id": branch_id,
        "Content-Type": "application/json",
    }

    # Prepare the models data
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
        upload_response = await client.post(
            f"{base_url}/v1/graphql",
            headers=headers,
            json={
                "query": """
                mutation CreateVersion($input: versions_insert_input!) {
                    insert_versions_one(object: $input) {
                        id
                        checksum
                        branch_id
                        dataschemas {
                            id
                            name
                            code
                        }
                    }
                }
                """,
                "variables": {
                    "input": {
                        "checksum": "1",  # You might want to generate a real checksum
                        "branch_id": branch_id,
                        "dataschemas": {"data": models_data},
                    }
                },
            },
        )
        upload_response.raise_for_status()
        response_data = upload_response.json()
        logger.info("Upload successful")
        return response_data
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise


async def main(
    base_url: str,
    login: str,
    password: str,
    datasource_id: str,
    branch_id: str,
    data_models_path: str,
):
    logger.info(f"Starting cube model upload process from {data_models_path}")
    models_path = Path(data_models_path)
    if not models_path.exists():
        logger.error(f"Models path not found: {data_models_path}")
        raise FileNotFoundError(f"Models path not found: {data_models_path}")

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            # Authenticate
            auth_data = await authenticate(client, base_url, login, password)

            # Scan for YAML files
            model_files = list(models_path.glob("*.yml")) + list(
                models_path.glob("*.yaml")
            )
            logger.info(f"Found {len(model_files)} YAML files")

            if not model_files:
                logger.warning("No YAML model files found in the specified directory")
                return

            # Process all model files
            valid_models = []
            for model_file in model_files:
                try:
                    logger.info(f"Processing file: {model_file.name}")
                    # Read and parse YAML file
                    with open(model_file, "r") as f:
                        yaml_content = f.read()
                        # Validate YAML structure
                        yaml_data = yaml.safe_load(yaml_content)
                        if not isinstance(yaml_data, dict) or "cubes" not in yaml_data:
                            logger.warning(f"Invalid cube model format in {model_file}")
                            continue

                        model = CubeModel(
                            name=model_file.stem,
                            version="1.0.0",
                            file_path=str(model_file),
                            code=yaml_content,
                        )
                        valid_models.append(model)
                        logger.info(
                            f"Successfully validated model file: {model_file.name}"
                        )

                except yaml.YAMLError as e:
                    logger.error(f"Failed to parse YAML file {model_file}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing {model_file.name}: {str(e)}")

            if valid_models:
                try:
                    # Upload all valid models in a single request
                    result = await upload_cube_models(
                        client,
                        base_url,
                        auth_data.access_token,
                        valid_models,
                        datasource_id,
                        branch_id,
                    )
                    logger.info(
                        f"Successfully uploaded {len(valid_models)} cube models"
                    )
                    logger.debug(f"Upload result: {result}")
                except httpx.HTTPError as e:
                    logger.error(f"Failed to upload models: {str(e)}")
            else:
                logger.warning("No valid models found to upload")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred: {str(e)}")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload OLAP cube models to the server"
    )
    parser.add_argument("--base-url", required=True, help="Base URL of the API")
    parser.add_argument("--login", required=True, help="User login")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument("--datasource-id", required=True, help="Datasource ID")
    parser.add_argument("--branch-id", required=True, help="Branch ID")
    parser.add_argument(
        "--data-models-path", required=True, help="Path to the YAML model files"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set debug level if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)

    asyncio.run(
        main(
            base_url=args.base_url,
            login=args.login,
            password=args.password,
            datasource_id=args.datasource_id,
            branch_id=args.branch_id,
            data_models_path=args.data_models_path,
        )
    )
