import flask
import os
from dotenv import find_dotenv, load_dotenv

app = flask.Flask(__name__)

load_dotenv(find_dotenv())


@app.route("/")
def index():
    return flask.render_template("index.html") #signup.html


app.run()
