import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from countries_data import COUNTRIES

START_DATE = datetime.date(2025, 4, 23)

app = Flask(__name__)

def create_app():
    """
    Create the Flask Application
    returns: app: the Flask application object
    """

    app = Flask(__name__)

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
        print(" * Error connecting to MongodDB", e)

    c_data = db["countries"]
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
    
    @app.route('/', methods=['GET', 'POST'])
    def home():
        guess = ""
        #country = get_today_country()
        #print(f"Today's country is: {country['name']}" if country else "No countries available.")
        if request.method == 'POST':
            guess = request.form.get('Guess')
            # You can process the guess here, e.g., check it against correct answers
            print(f"User guessed: {guess}")

        return render_template('home.html', guess=guess)
    
    return app


app = create_app()

if __name__ == "__main__":
    FLASK_PORT = os.getenv("FLASK_PORT", "8080")
    FLASK_ENV = os.getenv("FLASK_ENV")
    print(f"FLASK_ENV: {FLASK_ENV}, FLASK_PORT: {FLASK_PORT}")
    app.run(debug=False, host="0.0.0.0", port=int(FLASK_PORT))
