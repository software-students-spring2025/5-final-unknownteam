import datetime
from flask import Flask, render_template, request, jsonify, session
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from countries_data import COUNTRIES
from bson.regex import Regex

START_DATE = datetime.date(2025, 4, 23)

app = Flask(__name__)

def create_app():
    """
    Create the Flask Application
    returns: app: the Flask application object
    """

    app = Flask(__name__)
    app.secret_key = 'your_secret_key'

    load_dotenv()
    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_DBNAME = os.getenv('MONGO_DBNAME')

    cxn = MongoClient(MONGO_URI)
    db = cxn[MONGO_DBNAME]

    # testing for mongoDB connection
    try:
        cxn.admin.command("ping")
        print(" * Connected to MongoDB")
    except Exception as e:
        print(" * Error connecting to MongoDB", e)

    c_data = db["countries"]
    c_data.delete_many({})
    # Add country data to database
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
        session.clear()
        today_country = get_today_country()
        if today_country is None:
            return "No countries in database."

        session['target'] = {
            'name': today_country['name'],
            'population': today_country['population'],
            'area_km2': today_country['area_km2'],
            'gdp_per_capita_usd': today_country['gdp_per_capita_usd'],
            'languages': today_country['languages'],
            'continent': today_country['continent'],  # Include continent data
            'landlocked': today_country['landlocked']

        }
        session['row'] = 0
        session['guesses'] = []
        return render_template('home.html')

    @app.route('/guess', methods=['POST'])
    def guess():
        data = request.json['guesses']  # Single guess (the country name)
        target = session.get('target')  # The correct answer (full country info)
        row = session.get('row', 0)

        guess_value = data[0]  # User's text guess (like "Estonia")

        # Find the guessed country from the database
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

            if field in ['population', 'area_km2', 'gdp_per_capita_usd']:  # Numeric fields
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

            else:  # String fields (name, languages, continent)
                if str(guessed_value).strip().lower() == str(correct_value).strip().lower():
                    status = 'rectangleRight'
                display_value = str(guessed_value)

            feedback.append({
                'value': display_value,
                'status': status,
                'arrow': arrow
            })

        # Handle row increment and game over
        game_over = False
        message = ''
        if all(f['status'] == 'rectangleRight' for f in feedback):
            game_over = True
            message = 'You Win!'
        else:
            session['row'] = row + 1
            if session['row'] >= 6:
                game_over = True
                message = f"You Lose! The country was {target['name']}."

        return jsonify({
            'feedback': feedback,
            'row': row,
            'game_over': game_over,
            'message': message
        })

    @app.route('/autocomplete', methods=['GET'])
    def autocomplete():
        query = request.args.get('q', '').strip()

        if not query:
            return jsonify([])

        # Search countries that start with the input (case-insensitive)
        matches = c_data.find({'name': Regex(f'^{query}', 'i')})
        suggestions = [doc['name'] for doc in matches]

        return jsonify(suggestions)

    return app


app = create_app()

if __name__ == "__main__":
    FLASK_PORT = os.getenv("FLASK_PORT", "8080")
    FLASK_ENV = os.getenv("FLASK_ENV")
    print(f"FLASK_ENV: {FLASK_ENV}, FLASK_PORT: {FLASK_PORT}")
    app.run(debug=False, host="0.0.0.0", port=int(FLASK_PORT))
