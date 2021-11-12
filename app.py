import flask
import os
from dotenv import find_dotenv, load_dotenv

app = flask.Flask(__name__)

load_dotenv(find_dotenv())


@app.route("/")
def index():
    return flask.render_template("index.html") #signup.html

@app.route("/signup")
def signup():
    return flask.render_template("signup.html")

@app.route("/signup", methods=["POST"])
def register():
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")

    # we just need database to continue

    return flask.redirect("/") #change to login.html

@app.route("/quiz")
def quiz():
    return flask.render_template("quiz.html")


app.run()
