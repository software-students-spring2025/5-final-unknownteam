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

def test_signup_success(client):
    """Test successful user signup"""
    response = client.post('/signup', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Country Wordle' in response.data  

def test_signup_duplicate_user(client):
    """Test signup with existing username"""
    client.post('/signup', data={
        'username': 'testuser2',
        'password': 'testpass'
    })
    response = client.post('/signup', data={
        'username': 'testuser2',
        'password': 'testpass'
    })
    assert b'User already exists' in response.data

def test_signup_missing_fields(client):
    """Test signup with missing fields"""
    response = client.post('/signup', data={
        'username': '',
        'password': ''
    })
    assert b'Fill out both fields' in response.data

def test_login_success(client):
    """Test successful login"""
    client.post('/signup', data={
        'username': 'testuser3',
        'password': 'testpass'
    })
    response = client.post('/login', data={
        'username': 'testuser3',
        'password': 'testpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Country Wordle' in response.data  

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/login', data={
        'username': 'nonexistent',
        'password': 'wrongpass'
    })
    assert b'Invalid usernme or password' in response.data

def test_logout(client):
    """Test logout functionality"""

    client.post('/signup', data={
        'username': 'testuser4',
        'password': 'testpass'
    })

    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Country Wordle' in response.data  

def test_protected_route_requires_login(client):
    """Test that protected routes require login"""
    response = client.get('/logout')
    assert response.status_code == 302 
    assert b'login' in response.data.lower()

def test_handle_guess_correct(client):
    """Test handling a correct guess"""

    session = client.session_transaction()
    session['target'] = {
        'name': 'France',
        'population': 67000000,
        'area_km2': 643801,
        'gdp_per_capita_usd': 40000,
        'languages': ['French'],
        'continent': 'Europe',
        'landlocked': False
    }
    session['row'] = 0
    session['guesses'] = []
    session['mode'] = 'daily'
    session.commit()

    response = client.post('/guess', json={'guesses': ['France']})
    assert response.status_code == 200
    data = response.get_json()
    assert 'result' in data
    assert data['result'] == 'correct'

def test_handle_guess_incorrect(client):
    """Test handling an incorrect guess"""
    session = client.session_transaction()
    session['target'] = {
        'name': 'France',
        'population': 67000000,
        'area_km2': 643801,
        'gdp_per_capita_usd': 40000,
        'languages': ['French'],
        'continent': 'Europe',
        'landlocked': False
    }
    session['row'] = 0
    session['guesses'] = []
    session['mode'] = 'daily'
    session.commit()

    response = client.post('/guess', json={'guesses': ['Germany']})
    assert response.status_code == 200
    data = response.get_json()
    assert 'result' in data
    assert data['result'] == 'incorrect'
    assert 'hints' in data

def test_practice_guess(client):
    """Test practice mode guessing"""
    session = client.session_transaction()
    session['practice_target'] = {
        'name': 'Brazil',
        'population': 213000000,
        'area_km2': 8515767,
        'gdp_per_capita_usd': 15000,
        'languages': ['Portuguese'],
        'continent': 'South America',
        'landlocked': False
    }
    session['practice_row'] = 0
    session['practice_guesses'] = []
    session['mode'] = 'practice'
    session.commit()

    response = client.post('/practice_guess', json={'guesses': ['Brazil']})
    assert response.status_code == 200
    data = response.get_json()
    assert 'result' in data
    assert data['result'] == 'correct'

def test_get_possible_countries(client):
    """Test getting list of possible countries"""
    response = client.get('/get_possible_countries')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(isinstance(country, str) for country in data)

def test_autocomplete(client):
    """Test country name autocomplete"""
    response = client.get('/autocomplete?term=fra')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any('France' in country for country in data)

def test_get_today_country(client):
    """Test getting today's country"""
    response = client.get('/')
    assert response.status_code == 200
    session = client.session_transaction()
    assert 'target' in session
    assert isinstance(session['target'], dict)
    assert 'name' in session['target']