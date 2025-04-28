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
    assert b"Country Wordle" in response.data

def test_practice_page(client):
    """Test that practice page loads correctly"""
    response = client.get('/practice')
    assert response.status_code == 200
    assert b"Practice Mode" in response.data

def test_start_practice(client):
    """Test starting practice mode with filters"""
    payload = {
        "continent": ["Asia"],
        "population": ["large"],
        "area_size": ["large"],
        "hints": True
    }
    response = client.post('/start_practice', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "message" in data
    assert data["message"] == "Practice game started"

def test_practice_game_requires_start(client):
    """Test accessing practice_game without starting"""
    response = client.get('/practice_game')
    assert response.status_code == 400
    assert b"Please start a practice game first" in response.data


def test_get_practice_filters_no_filters(client):
    """Test getting practice filters when none are set"""
    response = client.get('/get_practice_filters')
    assert response.status_code == 400

def test_guess_invalid_country(client):
    """Test making a guess with an invalid country"""
    response = client.post('/guess', json={"guesses": ["Nonexistentland"]})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Country not found"

def test_get_possible_countries_no_filters(client):
    """Test getting possible countries with no filters"""
    response = client.get('/get_possible_countries')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list) or isinstance(data, dict)  # depending on what you return
