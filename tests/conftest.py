import os

import pytest

from dotenv import load_dotenv


# Load environment variables at the start of testing
load_dotenv()


# Make environment variables available to all tests
@pytest.fixture(scope="session")
def test_env():
    return {
        "TEST_EMAIL": os.getenv("TEST_EMAIL"),
        "TEST_PASSWORD": os.getenv("TEST_PASSWORD"),
        "TEST_API_URL": os.getenv("TEST_API_URL", "https://app.synmetrix.org"),
    }
