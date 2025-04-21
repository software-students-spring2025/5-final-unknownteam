from flask import (
    Flask,
    render_template as rt,
    request,
    redirect,
    url_for,
    flash,
)
from pymongo import MongoClient
import os
from dotenv import load_dotenv



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

    data = db.countries

    # testing for mongoDB connection
    try:
        cxn.admin.command("ping")
        print(" * Connected to MongoDB")
    except Exception as e:
        print(" * Error connecting to MongodDB", e)


    @app.route("/game", methods = ["GET", "POST"])
    def game():
        if request.method == "POST":
            guess = request.form["Guess a country!"]
            if not data["countries"].find_one({"name": guess}):
                flash("Invalid country.")
    
    return app


app = create_app()

if __name__ == "__main__":
    FLASK_PORT = os.getenv("FLASK_PORT", "5000")
    FLASK_ENV = os.getenv("FLASK_ENV")
    print(f"FLASK_ENV: {FLASK_ENV}, FLASK_PORT: {FLASK_PORT}")
    app.run(debug=True, host="0.0.0.0", port=int(FLASK_PORT))