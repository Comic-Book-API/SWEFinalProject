import flask
import os

app = flask.Flask(__name__)


@app.route("/")
def index():
    return flask.render_template("index.html")


app.run()
