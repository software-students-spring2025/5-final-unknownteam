import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Set up the test environment"""
    original_env = os.environ.copy()
    os.environ["TESTING"] = "true"
    yield
    os.environ.clear()
    os.environ.update(original_env)