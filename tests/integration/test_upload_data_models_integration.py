import os
import uuid

import pytest
import yaml

from synmetrix_python_client.auth import AuthClient
from synmetrix_python_client.graphql_client.client import Client
from synmetrix_python_client.graphql_client.input_types import (
    branches_insert_input,
    datasources_insert_input,
)
from synmetrix_python_client.use_cases.upload_data_models import main


@pytest.mark.skipif(
    not all([os.getenv("TEST_EMAIL"), os.getenv("TEST_PASSWORD")]),
    reason="Test credentials not provided in environment variables",
)
@pytest.mark.integration
class TestUploadDataModelsIntegration:
    @pytest.fixture
    def auth_client(self, test_env):
        """Create an AuthClient instance."""
        client = AuthClient(test_env["TEST_API_URL"])
        return client

    @pytest.fixture
    async def auth_tokens(self, auth_client, test_env):
        """Get auth tokens."""
        return await auth_client.login(
            email=test_env["TEST_EMAIL"],
            password=test_env["TEST_PASSWORD"],
        )

    @pytest.fixture
    async def graphql_client(self, auth_tokens, test_env):
        """Create authenticated GraphQL client."""
        tokens = await auth_tokens
        access_token = tokens.access_token

        client = Client(
            url=f"{test_env['TEST_API_URL']}/v1/graphql",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )
        return client, tokens

    @pytest.fixture
    def test_models_dir(self, tmp_path):
        """Create temporary directory with test YAML models."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        # Create test model file
        model = {
            "cubes": [
                {
                    "name": "Orders",
                    "sql": "SELECT * FROM public.orders",
                    "joins": [],
                    "dimensions": [
                        {
                            "name": "id",
                            "sql": "id",
                            "type": "number",
                            "primaryKey": True,
                        },
                        {"name": "status", "sql": "status", "type": "string"},
                        {"name": "createdAt", "sql": "created_at", "type": "time"},
                        {"name": "completedAt", "sql": "completed_at", "type": "time"},
                    ],
                    "measures": [
                        {"name": "count", "type": "count"},
                        {"name": "number", "sql": "number", "type": "sum"},
                    ],
                }
            ]
        }

        with open(models_dir / "orders.yml", "w") as f:
            yaml.dump(model, f, sort_keys=False)

        return models_dir

    @pytest.mark.asyncio
    async def test_upload_data_models_flow(
        self, graphql_client, test_models_dir, test_env
    ):
        """Test the complete flow of uploading data models."""

        datasource_id = None
        branch_id = None
        client, tokens = await graphql_client
        user_id = tokens.user_id

        try:
            user = await client.current_user(id=user_id)
            team_id = user.users_by_pk.members[0].team.id
            suffix = str(uuid.uuid4())[:4]

            # Create PostgreSQL data source with demo credentials
            object = datasources_insert_input(
                name="Test PostgreSQL " + suffix,
                db_type="POSTGRES",
                db_params={
                    "host": "demo-db-examples.cube.dev",
                    "port": 5432,
                    "database": "ecom",
                    "user": "cube",
                    "password": "12345",
                    "ssl": False,
                },
                team_id=team_id,
            )
            datasource = await client.create_data_source(object=object)
            datasource_id = datasource.insert_datasources_one.id
            assert datasource_id, "Failed to create data source"

            # Create a branch in the data source
            branch_name = "Test Branch " + suffix
            branch = await client.create_branch(
                object=branches_insert_input(
                    user_id=user_id,
                    datasource_id=datasource_id,
                    name=branch_name,
                    status="active",
                )
            )
            branch_id = branch.insert_branches_one.id
            assert branch_id, "Failed to create branch"

            # Upload models using the main function
            await main(
                base_url=test_env["TEST_API_URL"],
                datasource_id=datasource_id,
                branch_id=branch_id,
                data_models_path=str(test_models_dir),
                login=test_env["TEST_EMAIL"],
                password=test_env["TEST_PASSWORD"],
            )

            # Verify upload by checking the latest version
            version = await client.current_version(branch_id=branch_id)
            assert version.versions, "No versions found after upload"
            assert len(version.versions) == 1, "Expected exactly one version"

            # Verify model content
            dataschemas = version.versions[0].dataschemas
            assert len(dataschemas) == 1, "Expected one model"
            assert dataschemas[0].name == "orders.yml", "Model name mismatch"
        finally:
            # Clean up: delete the data source
            if datasource_id:
                await client.delete_data_source(id=datasource_id)
