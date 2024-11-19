import argparse
import asyncio
import hashlib
import logging

from pathlib import Path
from typing import Optional

import yaml

from pydantic import BaseModel

from synmetrix_python_client.auth import AuthClient, AuthTokens
from synmetrix_python_client.graphql_client import (
    CreateVersion,
    branches_bool_exp,
    dataschemas_arr_rel_insert_input,
    dataschemas_insert_input,
    datasources_bool_exp,
    uuid_comparison_exp,
    versions_insert_input,
)
from synmetrix_python_client.graphql_client.client import Client

from .utils import setup_logger


# Setup logging
logger = setup_logger()


class CubeModel(BaseModel):
    """Model representing a cube definition."""

    name: str
    file_path: str
    code: str


async def authenticate(base_url: str, login: str, password: str) -> AuthTokens:
    """Authenticate user and return tokens."""
    logger.info("Authenticating user...")
    auth_client = AuthClient(base_url)
    try:
        tokens = await auth_client.login(email=login, password=password)
        logger.info("Authentication successful")
        return tokens
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise


async def verify_branch(client: Client, datasource_id: str, branch_id: str) -> bool:
    """Verify that branch exists for the given datasource."""
    logger.info(f"Verifying branch {branch_id} for datasource {datasource_id}")
    try:
        # Query datasource
        datasource = await client.current_data_source(id=datasource_id)
        if not datasource.datasources_by_pk:
            logger.error(f"Datasource {datasource_id} not found")
            return False

        # Get all branches for this datasource using proper input types
        branches = await client.datasources(
            where=datasources_bool_exp(
                id=uuid_comparison_exp(_eq=datasource_id),
                branches=branches_bool_exp(id=uuid_comparison_exp(_eq=branch_id)),
            )
        )

        # Check if branch exists
        has_branch = any(
            b.id == branch_id for ds in branches.datasources for b in ds.branches
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
    user_id: str,
    datasource_id: str,
    branch_id: str,
) -> CreateVersion:
    """Upload cube models to the server."""
    logger.info(f"Uploading {len(models)} cube models...")

    models_data = [
        dataschemas_insert_input(
            user_id=user_id,
            name=model.name,
            code=model.code,
            datasource_id=datasource_id,
        )
        for model in models
    ]

    try:
        # Generate checksum from concatenated model codes
        checksum = hashlib.md5(
            "".join(model.code for model in models).encode()
        ).hexdigest()

        # Create version using proper input types
        version_input: versions_insert_input = versions_insert_input(
            user_id=user_id,
            checksum=checksum,
            branch_id=branch_id,
            dataschemas=dataschemas_arr_rel_insert_input(data=models_data),
        )
        result = await client.create_version(object=version_input)
        logger.info("Upload successful")
        logger.debug(f"Upload result: {result}")
        return result
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
) -> Optional[CreateVersion]:
    """Main entry point for the upload script."""
    logger.info(f"Starting cube model upload from {data_models_path}")
    models_path = Path(data_models_path)
    if not models_path.exists():
        msg = f"Models path not found: {data_models_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    # Get access token either from auth or direct input
    if not access_token and (login and password):
        tokens = await authenticate(base_url, login, password)
        access_token = tokens.access_token
    elif not access_token:
        msg = "Either access_token or login/password must be provided"
        logger.error(msg)
        raise ValueError(msg)

    jwt_payload = AuthClient.parse_access_token(access_token)
    user_id = jwt_payload["user_id"]

    # Initialize GraphQL client
    client = Client(
        url=f"{base_url}/v1/graphql",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # Verify branch exists for datasource
    if not await verify_branch(client, datasource_id, branch_id):
        raise ValueError(f"Branch {branch_id} not found for datasource {datasource_id}")

    try:
        yaml_files = [
            *models_path.glob("*.yml"),
            *models_path.glob("*.yaml"),
        ]
        logger.info(f"Found {len(yaml_files)} YAML files")

        if not yaml_files:
            logger.warning("No YAML model files found")
            return

        valid_models = []
        for model_file in yaml_files:
            try:
                logger.info(f"Processing: {model_file.name}")
                with open(model_file) as f:
                    yaml_content = f.read()
                    yaml_data = yaml.safe_load(yaml_content)
                    if not isinstance(yaml_data, dict):
                        logger.warning(f"Invalid format in {model_file}")
                        continue
                    if "cubes" not in yaml_data:
                        logger.warning(f"No cubes found in {model_file}")
                        continue

                    model = CubeModel(
                        name=model_file.name,
                        file_path=str(model_file),
                        code=yaml_content,
                    )
                    valid_models.append(model)
                    logger.info(f"Validated: {model_file.name}")

            except yaml.YAMLError as e:
                logger.error(f"YAML parse error in {model_file}: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing {model_file.name}: {str(e)}")

        if valid_models:
            result = await upload_cube_models(
                client, valid_models, user_id, datasource_id, branch_id
            )
            logger.info(f"Successfully uploaded {len(valid_models)} models")
            return result
        else:
            logger.warning("No valid models found")

    except Exception as e:
        logger.error(f"Upload process failed: {str(e)}")
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
