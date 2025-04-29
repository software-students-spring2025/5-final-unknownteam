import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
import os
import random
from dotenv import load_dotenv
from web_app.countries_data import COUNTRIES
from bson.regex import Regex
from bson.objectid import ObjectId
import requests
import flask_login

START_DATE = datetime.date(2025, 4, 23)

#app = Flask(__name__, template_folder="web_app/templates", static_folder="web_app/static")

def create_app():
    
    app = Flask(
        __name__,
        static_folder='static',    
        template_folder='templates' 
    )
    app.secret_key = 'your_secret_key'

    load_dotenv()
    MONGO_URI    = os.getenv('MONGO_URI', 'mongodb://mongodb:27017')
    MONGO_DBNAME = os.getenv('MONGO_DBNAME', 'country_wordle')

    cxn = MongoClient(MONGO_URI)
    db = cxn[MONGO_DBNAME]

    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    class User(flask_login.UserMixin):
        def __init__(self, id, username):
            self.id = id
            self.username = username

    @login_manager.user_loader
    def load_user(user_id):
        if db is not None:
            user_data = db.users.find_one({"_id": ObjectId(user_id)})
            if user_data:
                return User(user_id, user_data["username"])
        return None

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            if not username or not password:
                return render_template('signup.html', error="Please fill out both fields.")

            existing_user = db.users.find_one({"username": username})
            if existing_user:
                return render_template('signup.html', error="User already exists. Please log in instead.")

            # Insert the new user into the database
            result = db.users.insert_one({
                "username": username,
                "password": password,
                "wins": 0  # Initializing other fields if necessary
            })

            user = User(id=str(result.inserted_id), username=username)
            flask_login.login_user(user)
            return redirect(url_for('home'))

        return render_template('signup.html')


    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            user_data = db.users.find_one({"username": username})

            if user_data and user_data["password"] == password:
                user = User(id=str(user_data["_id"]), username=username)
                flask_login.login_user(user)
                return redirect(url_for('home'))
            else:
                return render_template('login.html', error="Invalid username or password.")

        return render_template('login.html')


    @app.route("/logout")
    @flask_login.login_required
    def logout():
        flask_login.logout_user()
        return redirect(url_for('home'))

    c_data = db["countries"]
    if c_data.count_documents({}) == 0:
        c_data.insert_many(COUNTRIES)
        print("Seeded countries collection.")
    else:
        print("Countries collection already populated.")

    def get_today_country():
        countries = list(c_data.find({}))
        if not countries:
            return None
        today = datetime.date.today()
        days_since_start = (today - START_DATE).days
        index = days_since_start % len(countries)
        return countries[index]

    @app.route('/')
    def home():
        today_country = get_today_country()
        if today_country is None:
            return "No countries in database."
        if today_country:
            today_country['_id'] = str(today_country['_id'])
        session['gameover']=False
        session['target'] = today_country
        session['mode'] = 'daily'
        session['row']=0
        session['guesses']=[]

        # Ensure guesses are retained for the day in session
        if flask_login.current_user.is_authenticated:
            user = load_user(flask_login.current_user.get_id())
            num = db.users.find_one({"username": user.username})["wins"]
            return render_template('home.html', mode='daily', login=True, nWins=num, guesses=session['guesses'], gameover=session['gameover'])
        else:
            return render_template('home.html', mode='daily', login=False, guesses=session['guesses'], gameover=session['gameover'])


    @app.route('/guess', methods=['POST'])
    def guess():
        data = request.get_json()
        if not data or 'guesses' not in data:
            return jsonify({"error": "Missing guesses"}), 400
        return handle_guess(mode='daily')


    @app.route('/practice')
    def practice():
        #print(session)
        session['gameover']=False
        session['practice_row'] = 0
        session['row']=0
        session['guesses']=0
        session['practice_guesses'] = []
        session['practice_target'] = None 
        session['practice_filters'] = {}
        session['guessed_countries'] = []
        #print(session)
        if(flask_login.current_user.is_authenticated):
            user = load_user(flask_login.current_user.get_id())
            num = db.users.find_one({"username":user.username})["wins"] 
            return render_template('practice.html',login=True, nWins=num)
        else:
            return render_template('practice.html',login = False)

    @app.route('/get_practice_filters', methods=['GET'])
    def get_practice_filters():
        filters = session.get('practice_filters')
        if not filters:
            return jsonify({}), 400
        return jsonify(filters)

    @app.route('/start_practice', methods=['POST'])
    def start_practice():
        filters = request.get_json()
        session['practice_filters'] = filters
        session['gameover']=False
        query = {}
        session['hint_enabled'] = filters.get('hints', False) if filters else False
        #print(filters)
        
        # Building conditions
        and_conditions = []

        if not filters or not any(filters.values()):
            # No filters selected, choosing a random country.
            matching_countries = list(c_data.find())
        else:
            if 'continent' in filters:
                continents = filters['continent']
                if len(continents) == 1:
                    # Single continent selected
                    query['continent'] = continents[0]
                elif len(continents) > 1:
                    # Multiple continents selected, use "$or" to match any continent
                    or_condition = [{'continent': c} for c in continents]
                    and_conditions.append({'$or': or_condition})
            if 'population' in filters:
                pop_conditions = []
                for size in filters['population']:
                    if size == 'small':
                        pop_conditions.append({'population': {'$lt': 10_000_000}})
                    elif size == 'medium':
                        pop_conditions.append({'population': {'$gte': 10_000_000, '$lte': 100_000_000}})
                    elif size == 'large':
                        pop_conditions.append({'population': {'$gt': 100_000_000}})
                if pop_conditions:
                    and_conditions.append({'$or': pop_conditions})

            if 'area_size' in filters:
                area_conditions = []
                for size in filters['area_size']:
                    if size == 'small':
                        area_conditions.append({'area_km2': {'$lt': 50_000}})
                    elif size == 'medium':
                        area_conditions.append({'area_km2': {'$gte': 50_000, '$lte': 1_000_000}})
                    elif size == 'large':
                        area_conditions.append({'area_km2': {'$gt': 1_000_000}})
                if area_conditions:
                    and_conditions.append({'$or': area_conditions})
            
            if and_conditions:
                query['$and'] = and_conditions

            matching_countries = list(c_data.find(query))
            matching_countries = [dict(t) for t in {tuple(d.items()) for d in matching_countries}]
            if not matching_countries:
                return jsonify({'error': 'No matching countries found.'}), 400

        chosen_country = random.choice(matching_countries)
        chosen_country['_id'] = str(chosen_country['_id'])
        session['practice_target'] = {
            'name': chosen_country['name'],
            'population': chosen_country['population'],
            'area_km2': chosen_country['area_km2'],
            'gdp_per_capita_usd': chosen_country['gdp_per_capita_usd'],
            'languages': chosen_country['languages'],
            'continent': chosen_country['continent'],
            'landlocked': chosen_country['landlocked']
        }
        session['mode'] = 'practice'
        session['practice_row'] = 0
        session['practice_guesses'] = []
        session['guessed_countries'] = []

        return jsonify({'message': 'Practice game started'})


    @app.route('/practice_game')
    def practice_game():
        session['gameover']=False
        session['row'] = 0
        query = {}
        session['guessed_countries'] = []

        if session.get('mode') != 'practice':
            return "Please start a practice game first.", 400

        filters = session.get('practice_filters')
        #print(filters)
        
        and_conditions = []

        if not filters or not any(filters.values()):
            matching_countries = list(c_data.find())
        else:
            if 'continent' in filters:
                continents = filters['continent']
                if len(continents) == 1:
                    query['continent'] = continents[0]
                elif len(continents) > 1:
                    or_condition = [{'continent': c} for c in continents]
                    and_conditions.append({'$or': or_condition})

            if 'population' in filters:
                pop_conditions = []
                for size in filters['population']:
                    if size == 'small':
                        pop_conditions.append({'population': {'$lt': 10_000_000}})
                    elif size == 'medium':
                        pop_conditions.append({'population': {'$gte': 10_000_000, '$lte': 100_000_000}})
                    elif size == 'large':
                        pop_conditions.append({'population': {'$gt': 100_000_000}})
                if pop_conditions:
                    and_conditions.append({'$or': pop_conditions})

            if 'area_size' in filters:
                area_conditions = []
                for size in filters['area_size']:
                    if size == 'small':
                        area_conditions.append({'area_km2': {'$lt': 50_000}})
                    elif size == 'medium':
                        area_conditions.append({'area_km2': {'$gte': 50_000, '$lte': 1_000_000}})
                    elif size == 'large':
                        area_conditions.append({'area_km2': {'$gt': 1_000_000}})
                if area_conditions:
                    and_conditions.append({'$or': area_conditions})

            if and_conditions:
                query['$and'] = and_conditions

            matching_countries = list(c_data.find(query))
            matching_countries = [dict(t) for t in {tuple(d.items()) for d in matching_countries}]
            if not matching_countries:
                return "No matching countries found.", 400

        chosen_country = random.choice(matching_countries)
        chosen_country['_id'] = str(chosen_country['_id'])

        session['practice_target'] = {
            'name': chosen_country['name'],
            'population': chosen_country['population'],
            'area_km2': chosen_country['area_km2'],
            'gdp_per_capita_usd': chosen_country['gdp_per_capita_usd'],
            'languages': chosen_country['languages'],
            'continent': chosen_country['continent'],
            'landlocked': chosen_country['landlocked']
        }

        session['practice_guesses'] = []
        if(flask_login.current_user.is_authenticated):
            user = load_user(flask_login.current_user.get_id())
            num = db.users.find_one({"username":user.username})["wins"] 
            return render_template('home.html', mode='practice', target=session.get('practice_target'), hint_enabled=session.get('hint_enabled', False),login=True, nWins = num, gameover=session['gameover'])
        else:
            return render_template('home.html', mode='practice', target=session.get('practice_target'), hint_enabled=session.get('hint_enabled', False),login = False, gameover=session['gameover'])

    @app.route('/practice_guess', methods=['POST'])
    def practice_guess():
        return handle_guess(mode='practice')


    @app.route('/guess_practice', methods=['POST'])
    def guess_practice():
        data = request.json['guesses']
        target = session.get('practice_target')
        row = session.get('practice_row', 0)

        guess_value = data[0]
        guessed_country = c_data.find_one({'name': {'$regex': f'^{guess_value}$', '$options': 'i'}})

        if not guessed_country:
            return jsonify({'error': 'Country not found'}), 400

        fields = ['name', 'continent', 'population', 'area_km2', 'gdp_per_capita_usd', 'languages', 'landlocked']
        feedback = []

        for field in fields:
            correct_value = target[field]
            guessed_value = guessed_country[field]

            status = 'rectangleWrong'
            arrow = None

            if field in ['population', 'area_km2', 'gdp_per_capita_usd']:
                try:
                    guess_num = float(guessed_value)
                    correct_num = float(correct_value)

                    if guess_num == correct_num:
                        status = 'rectangleRight'
                    elif guess_num < correct_num:
                        arrow = 'triangle-up'
                    else:
                        arrow = 'triangle-down'
                except ValueError:
                    pass
                display_value = '{:,}'.format(guessed_value) if field != 'gdp_per_capita_usd' else '{:,.2f}'.format(guessed_value)
            else:
                if str(guessed_value).strip().lower() == str(correct_value).strip().lower():
                    status = 'rectangleRight'
                display_value = str(guessed_value)

            feedback.append({
                'value': display_value,
                'status': status,
                'arrow': arrow
            })

        game_over = False
        message = ''
        if all(f['status'] == 'rectangleRight' for f in feedback):
            game_over = True
            message = 'You Win (Practice Mode)!'
            session['gameover']=True
        else:
            session['practice_row'] = row + 1
            if session['practice_row'] >= 6:
                game_over = True
                message = f"You Lose! The country was {target['name']}."
                session['gameover']=True

        return jsonify({
            'feedback': feedback,
            'row': row,
            'game_over': game_over,
            'gameover': session['gameover'],
            'message': message
        })

    def handle_guess(mode):
            mode = session.get('mode', 'daily')
            #print(f"Mode at guess handling: {mode}")
            if mode == 'practice':
                target = session.get('practice_target')
            else:
                target = session.get('target')
            data = request.json['guesses']
            row = session.get('row', 0)

            guess_value = data[0]

            query = {'name': {'$regex': f'^{guess_value}$', '$options': 'i'}}

            if mode == 'practice' and session.get('practice_countries'):
                query = {
                    'name': {'$in': session['practice_countries']},
                    '$and': [
                        {'name': {'$regex': f'^{guess_value}$', '$options': 'i'}}
                    ]
                }

            guessed_country = c_data.find_one(query)

            if not guessed_country:
                return jsonify({'error': 'Country not found'}), 400

            guessed_countries = session.get('guessed_countries', [])
            if guessed_country['name'] not in guessed_countries:
                guessed_countries.append(guessed_country['name'])
                session['guessed_countries'] = guessed_countries

            fields = ['name', 'continent', 'population', 'area_km2', 'gdp_per_capita_usd', 'languages', 'landlocked']
            feedback = []

            for field in fields:
                correct_value = target[field]
                guessed_value = guessed_country[field]

                status = 'rectangleWrong'
                arrow = None

                if field in ['population', 'area_km2', 'gdp_per_capita_usd']:
                    try:
                        guess_num = float(guessed_value)
                        correct_num = float(correct_value)

                        if guess_num == correct_num:
                            status = 'rectangleRight'
                        elif guess_num < correct_num:
                            arrow = 'triangle-up'
                        else:
                            arrow = 'triangle-down'
                    except ValueError:
                        pass
                    display_value = '{:,}'.format(guessed_value) if field != 'gdp_per_capita_usd' else '{:,.2f}'.format(guessed_value)

                else:
                    if str(guessed_value).strip().lower() == str(correct_value).strip().lower():
                        status = 'rectangleRight'
                    display_value = str(guessed_value)

                feedback.append({
                    'value': display_value,
                    'status': status,
                    'arrow': arrow
                })

            game_over = False
            message = ''
            if all(f['status'] == 'rectangleRight' for f in feedback):
                game_over = True
                message = 'You Win! You have successfully guessed the country!'
                session['gameover']=True
                if(flask_login.current_user.is_authenticated) and mode == 'daily':
                    user = load_user(flask_login.current_user.get_id())
                    num = db.users.find_one({"username":user.username})["wins"] + 1
                    db.users.update_one({"username":user.username},{"$set":{"wins":num}})
                    print(num)
                    return jsonify({
                        'feedback': feedback,
                        'row': row,
                        'game_over': game_over,
                        'gameover': session['gameover'],
                        'message': message,
                        'target': target,
                        'Nwins': num
                    })
                if(flask_login.current_user.is_authenticated):
                    user = load_user(flask_login.current_user.get_id())
                    num = db.users.find_one({"username":user.username})["wins"]
                    db.users.update_one({"username":user.username},{"$set":{"wins":num}})
                    return jsonify({
                        'feedback': feedback,
                        'row': row,
                        'game_over': game_over,
                        'gameover': session['gameover'],
                        'message': message,
                        'target': target,
                        'Nwins': num
                    })
                else:
                    return jsonify({
                        'feedback': feedback,
                        'row': row,
                        'game_over': game_over,
                        'gameover': session['gameover'],
                        'message': message,
                        'target': target,
                    })
            else:
                session['row'] = row + 1
                if session['row'] >= 6:
                    session['gameover']=True
                    game_over = True
                    message = f"You Lose! The country was {target['name']}."
                return jsonify({
                    'feedback': feedback,
                    'row': row,
                    'game_over': game_over,
                    'gameover': session['gameover'],
                    'message': message,
                    'target': target,
                })
            
    
    @app.route('/get_possible_countries', methods=['GET'])
    def get_possible_countries():
        filters = session.get('practice_filters', {})
        guessed_countries = session.get('guessed_countries', [])
        practice_target = session.get('practice_target', {})

        query = {}
        and_conditions = []

        non_numeric_fields = ['continent', 'languages', 'landlocked']
        numeric_fields = ['population', 'area_km2', 'gdp_per_capita_usd']

        if guessed_countries:
            for guessed_country_name in guessed_countries:
                guessed_country = c_data.find_one({'name': {'$regex': f'^{guessed_country_name}$', '$options': 'i'}})
                if guessed_country:
                    for field in non_numeric_fields:
                        if field in guessed_country and field in practice_target:
                            guessed_value = guessed_country[field]
                            target_value = practice_target[field]

                            if guessed_value == target_value:
                                and_conditions.append({field: guessed_value})
                            else:
                                and_conditions.append({field: {'$ne': guessed_value}})

                    for field in numeric_fields:
                        if field in guessed_country and field in practice_target:
                            guessed_value = guessed_country[field]
                            target_value = practice_target[field]

                            if guessed_value > target_value:
                                and_conditions.append({field: {'$lt': guessed_value}})
                            elif guessed_value < target_value:
                                and_conditions.append({field: {'$gt': guessed_value}})

            if guessed_countries:
                and_conditions.append({'name': {'$nin': guessed_countries}})

        # Area size
        if 'area_size' in filters:
            area_conditions = []
            for size in filters['area_size']:
                if size == 'small':
                    area_conditions.append({'area_km2': {'$lt': 50_000}})
                elif size == 'medium':
                    area_conditions.append({'area_km2': {'$gte': 50_000, '$lte': 1_000_000}})
                elif size == 'large':
                    area_conditions.append({'area_km2': {'$gt': 1_000_000}})
            if area_conditions:
                and_conditions.append({'$or': area_conditions})

        # Population filter handling
        if 'population' in filters:
            pop_conditions = []
            for size in filters['population']:
                if size == 'small':
                    pop_conditions.append({'population': {'$lt': 10_000_000}})
                elif size == 'medium':
                    pop_conditions.append({'population': {'$gte': 10_000_000, '$lte': 100_000_000}})
                elif size == 'large':
                    pop_conditions.append({'population': {'$gt': 100_000_000}})
            if pop_conditions:
                and_conditions.append({'$or': pop_conditions})

        # Continent filters
        if 'continent' in filters:
            continents = filters['continent']
            if len(continents) == 1:
                and_conditions.append({'continent': continents[0]})
            elif len(continents) > 1:
                or_condition = [{'continent': c} for c in continents]
                and_conditions.append({'$or': or_condition})

        if and_conditions:
            query = {'$and': and_conditions}
        else:
            query = {}
        #print(query)
        possible_countries = list(c_data.find(query))

        for country in possible_countries:
            country['_id'] = str(country['_id'])

        return jsonify({'countries': possible_countries})

    @app.route('/autocomplete', methods=['GET'])
    def autocomplete():
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify([])
        
        search_query = {'name': Regex(f'^{query}', 'i')}
        
        if session.get('mode') == 'practice' and session.get('practice_countries'):
            search_query['name'] = {'$in': session['practice_countries']}
            search_query['name']['$regex'] = f'^{query}'
            search_query['$options'] = 'i'

        matches = c_data.find(search_query)
        suggestions = [doc['name'] for doc in matches]
        return jsonify(suggestions)
    
    return app

if __name__ == "__main__":
    app = create_app()
    FLASK_PORT = os.getenv("FLASK_PORT", "8080")
    FLASK_ENV = os.getenv("FLASK_ENV")
    print(f"FLASK_ENV: {FLASK_ENV}, FLASK_PORT: {FLASK_PORT}")
    app.run(debug=False, host="0.0.0.0", port=int(FLASK_PORT))