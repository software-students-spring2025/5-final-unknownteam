import pytest
from web_app.app import create_app

@pytest.fixture
def client():
    """Setup test Flask app"""
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

def test_homepage(client):
    """Test that homepage loads correctly"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Country Guesser" in response.data

def test_practice_page(client):
    """Test that practice page loads correctly"""
    response = client.get('/practice')
    assert response.status_code == 200
    assert b"Practice Mode" in response.data
