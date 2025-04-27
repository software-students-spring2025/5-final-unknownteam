import sys
import os
import pytest
from unittest.mock import MagicMock, patch
sys.path.append(os.path.abspath("./web-app"))
import app
import io

#  package for creating mock mongoDB databases
@pytest.fixture
def mongoDB_simulation():
    """Simulates mongoDB database"""
    users = MagicMock()
    entries = MagicMock()
    db = MagicMock()
    db.__getitem__.side_effect = lambda x: users if x == "users" else entries
    with patch('app.DB', db), \
            patch('app.COLLECTION', entries):
        yield (users, entries)


@pytest.fixture
def client():
    """Setup test Flask app"""
    app.app.config["TESTING"] = True
    app.app.config["WTF_CSRF_ENABLED"] = False
    with app.app.test_client() as test_client:
        yield test_client
