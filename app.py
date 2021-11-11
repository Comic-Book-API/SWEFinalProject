import os
import hashlib
from dotenv import find_dotenv, load_dotenv
import flask_login
import flask
from flask import Flask, render_template, request
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

load_dotenv(find_dotenv())

SECRET_KEY = os.getenv("SECRET_KEY")


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("HEROKU_DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = str.encode(SECRET_KEY)

login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy(app)


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    authenticated = False

    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

    def __repr__(self):
        return "<username: '{0}'> <password: '{1}'>".format(self.username, self.password)


db.create_all()


@login_manager.user_loader
def user_loader(username):
    user = Person.query.get(username)
    return user if user else None


@app.route('/', methods=['POST', 'GET'])
def sign_in():
    if flask.request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        user = Person.query.filter_by(username=username, password=password_hash).first()
        if user:
            user.authenticated = True
            flask_login.login_user(user)
            return flask.redirect('/info')

    return render_template('login.html')


@app.route('/signup', methods=['POST', 'GET'])
def signup_post():
    if flask.request.method == 'POST':
        id = db.session.query(Person).count() + 1
        username = flask.request.form.get('username')
        password = request.form.get('password')
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        user_exists = db.session.query(db.exists().where(Person.username == username)).scalar()

        if user_exists:
            flask.flash('Username already exists')
            return flask.redirect('/signup')

        else:
            user = Person(id=id, username=username, password=password_hash)
            db.session.add(user)
            db.session.commit()

            flask.flash('Signup successful!')
            return flask.redirect('/')

    return flask.render_template('signup.html')


@app.route('/info', methods=['POST', 'GET'])
@flask_login.login_required
def reload_init():
    return render_template('hi.html')


app.run(host='0.0.0.0',
        port=os.getenv("PORT", 8080),
        use_reloader=True)

