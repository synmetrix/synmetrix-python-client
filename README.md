# Synmetrix GraphQL Client

A Python GraphQL client library for interacting with the Synmetrix API.

## Features

- Fully typed async GraphQL client
- Automatic query generation
- WebSocket subscription support
- Comprehensive API documentation

## Installation

### Using pip

```bash
pip install synmetrix-graphql-client
```

### Using poetry

```bash
poetry add synmetrix-graphql-client
```

## Quick Start

```python
import asyncio
import jwt
from synmetrix_graphql_client import Client

# Decode JWT token to get user_id
access_token = "your_access_token"
jwt_payload = jwt.decode(access_token, options={"verify_signature": False})
user_id = jwt_payload.get("hasura", {}).get("x-hasura-user-id")

# Initialize client
client = Client(
    url="https://api.synmetrix.org/v1/graphql",
    headers={"Authorization": f"Bearer {access_token}"},
)

async def get_current_user():
    # Query current user
    current_user = await client.current_user(id=user_id)
    print(f"User: {current_user.users_by_pk.display_name}")
    
    # Subscribe to user updates
    async for update in client.sub_current_user(id=user_id):
        print(f"Update received: {update.users_by_pk.display_name}")

# Run the example
asyncio.run(get_current_user())
```

## API Reference

### Common Methods

#### User Management
- `async def current_user(id: Any) -> CurrentUser`
  Get current user information

- `async def sub_current_user(id: Any) -> AsyncIterator[SubCurrentUser]`
  Subscribe to user updates

#### Team Management
- `async def create_team(name: str) -> CreateTeam`
  Create a new team

- `async def current_team(id: Any) -> CurrentTeam`
  Get current team information

- `async def team_data(team_id: Any) -> TeamData`
  Get detailed team data

#### Data Source Operations
- `async def create_data_source(object: datasources_insert_input) -> CreateDataSource`
  Create a new data source

- `async def current_data_source(id: Any) -> CurrentDataSource`
  Get current data source information

- `async def check_connection(id: Any) -> CheckConnection`
  Check data source connection

#### Access Management
- `async def create_access_list(object: access_lists_insert_input) -> CreateAccessList`
  Create new access list

- `async def update_access_list(pk_columns, set) -> UpdateAccessList`
  Update existing access list

For the complete API reference, see [API Reference](docs/api_reference.md).

## Development

### Prerequisites

- Python 3.8+
- Poetry (Python package manager)

### Setting up the development environment

1. Clone the repository:
```bash
git clone https://github.com/synmetrix/synmetrix-graphql-client.git
cd synmetrix-graphql-client
```

2. Install dependencies:
```bash
poetry install
```

3. Activate the virtual environment:
```bash
poetry shell
```

### Running Tests

```bash
poetry run pytest
```

### Generating API Documentation

```bash
./scripts/generate_api_docs.py
```

### Publishing to PyPI

1. Test PyPI release:
```bash
./scripts/push_to_testpypi.sh
```

2. Production PyPI release:
```bash
./scripts/push_to_pypi.sh
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:
- Open an issue in the GitHub repository
- Contact us at support@synmetrix.org
- Visit our documentation at https://docs.synmetrix.org