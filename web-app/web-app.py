from flask import (
    Flask,
    render_template as rt,
    request,
    redirect,
    url_for,
    flash,
)
from pymongo import MongoClient

CLIENT = MongoClient("mongodb://mongodb:27017/")
DB = CLIENT["unknownteam"]
COLLECTION = DB["countries"]


app = Flask(__name__)


@app.route("/game", methods = ["GET", "POST"])
def game():
    if request.method == "POST":
        guess = request.form["Guess a country!"]
        if not DB["countries"].find_one({"name": guess}):
            flash("Invalid country.")
