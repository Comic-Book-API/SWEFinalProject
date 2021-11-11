import flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import find_dotenv, load_dotenv


app = flask.Flask(__name__)

load_dotenv(find_dotenv())

# database location
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://tmp.db"
# Database config and setup
db = SQLAlchemy(app)

class Account(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.BigInteger, nullable=False)
    # The following fields encode a list of up to 20 id's into a string.
    # This code assumes that the max length for any one of these ids is 8 digits/characters

    DC_comics = db.Column(db.String(200))
    Marvel_comics = db.Column(db.String(200))
    DC_characters = db.Column(db.String(200))
    Marvel_characters = db.Column(db.String(200))

db.create_all()
db.session.commit()


@app.route("/")
def index():
    return flask.render_template("index.html") #signup.html


app.run()
