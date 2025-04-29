import pytest
from app import create_app

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
    assert isinstance(data, list) or isinstance(data, dict)

def test_start_practice_missing_payload(client):
    """Test starting practice mode with no payload"""
    response = client.post('/start_practice', json={})
    assert response.status_code == 200

def test_guess_no_payload(client):
    """Test making a guess with missing guesses payload"""
    response = client.post('/guess', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_guess_wrong_payload_type(client):
    """Test making a guess with wrong payload structure"""
    response = client.post('/guess', json={"guesses": "France"})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_practice_filters_after_start(client):
    """Test getting practice filters after starting practice"""
    payload = {
        "continent": ["Europe"],
        "population": ["small"],
        "area_size": ["small"],
        "hints": False
    }
    client.post('/start_practice', json=payload)
    response = client.get('/get_practice_filters')
    assert response.status_code == 200
    filters = response.get_json()
    assert "continent" in filters
    assert filters["continent"] == ["Europe"]

def test_practice_game_after_start(client):
    """Test accessing practice_game after starting"""
    payload = {
        "continent": ["Africa"],
        "population": ["medium"],
        "area_size": ["medium"],
        "hints": True
    }
    client.post('/start_practice', json=payload)
    response = client.get('/practice_game')
    assert response.status_code == 200
    assert b"Practice Mode" in response.data or b"practice" in response.data.lower()

def test_404_not_found(client):
    """Test non-existent route returns 404"""
    response = client.get('/thispagedoesnotexist')
    assert response.status_code == 404

def test_homepage_contains_input(client):
    """Test homepage contains guess input field"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'<input' in response.data

def test_signup(client):
    """Tests signup functionality"""
    payload = {
        "username": ["ExampleUser"],
        "password": ["Password"],
        "wins": [0]
    }
    response = client.post('/signup',json = payload)
    assert response.status_code == 200 or response.status_code == 302

def test_login_page(client):
    """Test that login page loads correctly"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Login" in response.data

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    payload = {
        "username": "InvalidUser",
        "password": "WrongPassword"
    }
    response = client.post('/login', json=payload)
    assert response.status_code == 200
    assert b"Invalid" in response.data or response.status_code == 401

def test_logout_requires_login(client):
    """Test logout requires login"""
    response = client.get('/logout')
    assert response.status_code == 302  # Should redirect to login

def test_autocomplete_empty_query(client):
    """Test autocomplete with empty query"""
    response = client.get('/autocomplete?query=')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_autocomplete_valid_query(client):
    """Test autocomplete with valid query"""
    response = client.get('/autocomplete?query=Uni')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_guess_practice_no_session(client):
    """Test practice guess without session data"""
    response = client.post('/guess_practice', json={"guesses": ["France"]})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_get_possible_countries_with_filters(client):
    """Test getting possible countries with filters"""
    payload = {
        "continent": ["Europe"],
        "population": ["medium"],
        "area_size": ["small"]
    }
    client.post('/start_practice', json=payload)
    response = client.get('/get_possible_countries')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list) or isinstance(data, dict)

def test_practice_guess_invalid_country(client):
    """Test practice guess with invalid country"""
    payload = {
        "continent": ["Europe"],
        "population": ["medium"],
        "area_size": ["small"]
    }
    client.post('/start_practice', json=payload)
    response = client.post('/practice_guess', json={"guesses": ["Nonexistentland"]})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_practice_guess_correct_country(client):
    """Test practice guess with correct country"""
    payload = {
        "continent": ["Europe"],
        "population": ["medium"],
        "area_size": ["small"]
    }
    client.post('/start_practice', json=payload)
    response = client.post('/practice_guess', json={"guesses": ["France"]})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)

def test_session_persistence(client):
    """Test that session data persists between requests"""
    payload = {
        "continent": ["Asia"],
        "population": ["large"],
        "area_size": ["large"]
    }
    client.post('/start_practice', json=payload)
    response = client.get('/get_practice_filters')
    assert response.status_code == 200
    filters = response.get_json()
    assert "continent" in filters
    assert filters["continent"] == ["Asia"]

