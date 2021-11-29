import flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import os
import getpass
from dotenv import find_dotenv, load_dotenv
from cryptography.fernet import Fernet
from flask_login import LoginManager, login_user, login_required
import flask_login
import marvel_api as marvel

app = flask.Flask(__name__)
app.secret_key = "this is the most secretive key in the universe!!!"

login_manager = LoginManager()
login_manager.init_app(app)


load_dotenv(find_dotenv())


CRYPTOGRAPHY_KEY = os.getenv("CRYPTO_KEY").encode("UTF-8")
encryption_engine = Fernet(CRYPTOGRAPHY_KEY)
# database location

engine = create_engine(
    "postgresql://hxbfjmfvfojzkv:f307f9122a40563211c43b4bbbf03e8ac9e8e2d3c0525aa3b1b462ee2ca48810@ec2-23-23-133-10.compute-1.amazonaws.com:5432/d9nffekjuq21dl"
)  # ("postgresql://localhost/tmp.db")
if not database_exists(engine.url):
    create_database(engine.url)

app.config["SQLALCHEMY_DATABASE_URI"] = engine.url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # overhead is bad
# Database config and setup
db = SQLAlchemy(app)
MAX_ID_ENTRIES = (
    20  # If this value is made greater, the database must be completely reinitialized
)


class Account(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    # The following fields encode a list of up to 20 id's into a string.
    # This code assumes that the max length for any one of these ids is 8 digits/characters
    # the encoding for this is very simple. each item is separated by ;'s
    # for example, "1234;5351;1234;413234;41234124"
    comics = db.Column(db.String(200), nullable=False)
    characters = db.Column(db.String(200), nullable=False)

    # Login stuff
    authenticated = False

    def is_active(self):
        return True

    def get_id(self):
        return self.uid

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False


# Login functions
@login_manager.user_loader
def user_loader(uid):
    user = Account.query.filter_by(uid=uid).first()
    if user:
        return user
    else:
        return None


db.create_all()
db.session.commit()

# returns encrypted hash
def encrypt(word):
    word = word.encode("UTF-8")
    hash = encryption_engine.encrypt(word)
    hash = hash.decode("UTF-8")
    return hash


# decrypts the given hash, returning the strign which was originally encrypted
def decrypt(hash):
    hash = hash.encode("UTF-8")
    word = encryption_engine.decrypt(hash)
    word = word.decode("UTF-8")
    return word


# adds a new account to the database.
# Make sure password is encrypted!!
# returns 0 if successful, -1 if the username already exists
def add_account(username, password):
    new_acc = Account(username=username, password=password, comics="", characters="")
    test_acc = Account.query.filter_by(username=username).first()
    if test_acc is not None:
        if test_acc.username == username:
            return -1
    db.session.add(new_acc)
    db.session.commit()
    return 0


# removes comic from the comics entry for the given user
# returns 0 if successful, -1 if the comic could not be found
def remove_comic(uid, comic_id):
    comics = decode_string(get_account_db_comics(uid))
    if comics.count(comic_id) == 0:
        return -1
    comics.remove(comic_id)
    get_account_db_entry(uid).comics = encode_string(comics)
    db.session.commit()
    return 0


# removes character from the characters entry for the given user
# returns 0 if successful, -1 if the entry could not be found
def remove_character(uid, character_id):
    characters = decode_string(get_account_db_characters(uid))
    if characters.count(character_id) == 0:
        return -1
    characters.remove(character_id)
    get_account_db_entry(uid).characters = encode_string(characters)
    db.session.commit()
    return 0


# adds comic from the comics entry for the given user
# returns 0 if successful, -1 if the entry could not be added because the max has been reached, and -2 if the entry is already present
def add_comic(uid, comic_id):
    comics = decode_string(get_account_db_comics(uid))
    if len(comics) >= 20:
        return -1
    if comics.count(comic_id) > 0:
        return -2
    comics.append(comic_id)
    get_account_db_entry(uid).comics = encode_string(comics)
    db.session.commit()
    return 0


# adds character from the character entry for the given user
# returns 0 if successful, -1 if the entry could not be added because the max has been reached, and -2 if the entry is already present
def add_character(uid, character_id):
    characters = decode_string(get_account_db_characters(uid))

    if len(characters) >= 20:
        return -1
    if characters.count(character_id) > 0:
        return -2
    characters.append(character_id)
    get_account_db_entry(uid).characters = encode_string(characters)
    db.session.commit()
    return 0


# decodes a string, returning the encoded list of ids
# return value of None means that the encoded string is invalid somehow
def decode_string(encoded_string):
    if encoded_string == "":
        return []
    id_list = encoded_string.split(";")
    # verification tests:
    for id in id_list:
        # no id should be empty
        if len(id) == 0:
            return None
        # all chars should be numbers
        if not id.isdecimal():
            return None
    return id_list


# returns the character at the given index
def get_character(uid, character_index):
    characters = decode_string(get_account_db_characters(uid))
    return characters[character_index]


# returns the comci at the given index
def get_comic(uid, comic_index):
    comics = decode_string(get_account_db_comics(uid))
    return comics[comic_index]


# encodes a string for storage in the database
def encode_string(id_list):
    ids_str = ""
    for id in id_list:
        if len(ids_str) != 0:
            ids_str += ";"
        ids_str += id
    return ids_str


# returns the UID of the given username.
# returns -1 if the username doesn't exist in the database.
def uid_by_username(username):
    acc = Account.query.filter_by(username=username).first()
    if acc is None:
        return -1
    else:
        return acc.uid


# returns the account object associated with the given UID
def get_account_db_entry(uid):
    acc = Account.query.filter_by(uid=uid).first()
    return acc


# returns the stored comics, will need to be decoded
def get_account_db_comics(uid):
    return get_account_db_entry(uid).comics


# returns the stored characters, will need to be decoded
def get_account_db_characters(uid):
    return get_account_db_entry(uid).characters


@app.route("/logout")
@login_required
def logout():
    flask_login.logout_user()
    return flask.render_template("logout.html")


@app.route("/search", methods=["POST", "GET"])
def search():
    if flask.request.method == "GET":
        return flask.render_template("search.html")
    if flask.request.method == "POST":
        search = flask.request.form["search"]
        imgUnavailable = "http://i.annihil.us/u/prod/marvel/i/mg/b/40/image_not_available/standard_fantastic.jpg"
        titleArr = []
        imgArr = []
        creatorArr = []
        onSaleArr = []
        buyLinkArr = []
        for i in range(10):
            if marvel.getComicByTitle(search, i) != False:
                (
                    title,
                    creatorList,
                    onSaleDate,
                    imgLink,
                    buyLink,
                ) = marvel.getComicByTitle(search, i)
                if imgLink == imgUnavailable:
                    imgLink = "/static/comic error message.png"
                titleArr.append(title)
                imgArr.append(imgLink)
                creatorArr.append(creatorList)
                onSaleArr.append(onSaleDate)
                buyLinkArr.append(buyLink)
        if len(titleArr) == 0:
            flask.flash("Bad search parameters, please try again!")

        return flask.render_template(
            "search.html",
            titles=titleArr,
            imgLinks=imgArr,
            creators=creatorArr,
            onSaleDates=onSaleArr,
            buyLinks=buyLinkArr,
        )


@app.route("/characterinfo", methods=["POST", "GET"])
def characterinfo():
    return flask.render_template("characterInfo.html")


@app.route("/comicinfo", methods=["POST", "GET"])
def comicinfo():
    return flask.render_template("comicInfo.html")


@app.route("/filter", methods=["POST"])
def setFilter():
    choice = flask.request.form["option"]
    return flask.redirect(flask.url_for("search", choice=choice))


@app.route("/")
def index():
    return flask.render_template("index.html")  # signup.html


@app.route("/signup")
def signup():
    return flask.render_template("signup.html")


@app.route("/signup", methods=["POST"])
def register():
    username = flask.request.form.get("username")
    password = encrypt(flask.request.form.get("password"))
    if add_account(username, password) == -1:
        flask.flash("That username is taken!")
        return flask.redirect("/signup")
    else:
        add_account(username, password)
        flask.flash("Sucessful signup!")

    # we just need database to continue

    return flask.redirect("/")  # change to login.html


@app.route("/quiz")
def quiz():
    return flask.render_template("quiz.html")


@app.route("/login", methods=["POST", "GET"])
def sign_in():
    if flask.request.method == "POST":
        username = flask.request.form.get("username")
        password = flask.request.form.get("password")
        user = Account.query.filter_by(username=username).first()
        print(username)
        if user:
            if password == decrypt(user.password):
                user.authenticated = True
                print(user)
                flask_login.login_user(user)
                flask.flash("Successfully logged in!")
                return flask.redirect("/")
            else:
                flask.flash("Incorrect username/password!")
                return flask.redirect("/login")
        else:
            flask.flash("Incorrect username/password!")
            return flask.redirect("/login")
    return flask.render_template("login.html")


@app.route("/characters", methods=["POST", "GET"])
def characters():
    if flask.request.method == "GET":
        return flask.render_template("characters.html")
    if flask.request.method == "POST":
        search = flask.request.form["search"]
        resultArr = []
        resultArr2 = []
        for i in range(10):
            if marvel.getCharacter(search, i) != False:
                (id, name, description, imgLink) = marvel.getCharacter(search, i)
                if (
                    imgLink
                    == "http://i.annihil.us/u/prod/marvel/i/mg/b/40/image_not_available/standard_fantastic.jpg"
                ):
                    imgLink = "/static/comic error message.png"
                resultArr.append(name)
                resultArr2.append(imgLink)
        if len(resultArr) == 0:
            flask.flash("Bad search parameters, please try again!")
        return flask.render_template(
            "characters.html", titles=resultArr, imgLinks=resultArr2
        )
    return flask.render_template("characters.html")


@app.route("/comicInfo", methods=["POST", "GET"])
def comicInfo():
    return flask.render_template("comicInfo.html")


@app.route("/characterInfo", methods=["POST", "GET"])
def characterInfo():
    return flask.render_template("characterInfo.html")


app.run(host="0.0.0.0", port=os.getenv("PORT", 8080), use_reloader=True)
