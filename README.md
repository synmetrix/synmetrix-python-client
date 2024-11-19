# Synmetrix Python Client

A Python client library for interacting with the Synmetrix API.

### Key Components

1. **GraphQL Client**
   - Fully typed async client for GraphQL operations
   - WebSocket subscription support
   - Automatic query generation
   - Error handling and response validation

2. **Authentication Client**
   - JWT token management
   - User authentication flows
   - Session handling
   - Password management

## Installation

### Using pip

```bash
pip install synmetrix-python-client
```

### Using poetry

```bash
poetry add synmetrix-python-client
```

## Quick Start

```python
import asyncio
from synmetrix_python_client.graphql_client import Client
from synmetrix_python_client.auth import AuthClient

# Decode JWT token to get user_id
access_token = "your_access_token"
jwt_payload = AuthClient.parse_access_token(access_token)
user_id = jwt_payload["user_id"]

# Initialize client
client = Client(
    url="https://app.synmetrix.org/v1/graphql",
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

## Documentation

### API Reference

The library provides comprehensive API documentation in the following formats:

- **HTML Documentation**: Browse the full API reference at [docs/src/synmetrix_python_client/](docs/src/synmetrix_python_client/)
  - GraphQL Client API: [docs/src/synmetrix_python_client/graphql_client/client.html](docs/src/synmetrix_python_client/graphql_client/client.html)
  - Authentication API: [docs/src/synmetrix_python_client/auth.html](docs/src/synmetrix_python_client/auth.html)

## Development

### Prerequisites

- Python 3.9+
- Poetry (Python package manager)

### Setting up the development environment

1. Clone the repository:
```bash
git clone https://github.com/ifokeev/synmetrix-python-client.git
cd synmetrix-python-client
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

### Generating Documentation

To regenerate the documentation:

```bash
./scripts/generate_graphql_api_docs.sh # GraphQL documentation
./scripts/generate_auth_api_docs.sh    # Auth documentation
```

### Publishing to PyPI

1. Test PyPI release:
```bash
./scripts/push_to_testpypi.sh YOUR_PYPI_TOKEN
```

2. Production PyPI release:
```bash
./scripts/push_to_pypi.sh YOUR_PYPI_TOKEN
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

## Examples

For complete working examples of client usage, check the [`use_cases/`](src/synmetrix_python_client/use_cases/) directory in the repository.
