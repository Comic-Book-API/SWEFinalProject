import flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import os
import getpass
from dotenv import find_dotenv, load_dotenv
from cryptography.fernet import Fernet
from flask_login import LoginManager, login_user, login_required, current_user
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


def encrypt(word):
    """# returns encrypted hash"""
    word = word.encode("UTF-8")
    local_hash = encryption_engine.encrypt(word)
    local_hash = hash.decode("UTF-8")
    return local_hash


def decrypt(local_hash):
    """# decrypts the given hash, returning the strign which was originally encrypted"""
    local_hash = local_hash.encode("UTF-8")
    word = encryption_engine.decrypt(local_hash)
    word = word.decode("UTF-8")
    return word


def add_account(username, password):
    """# adds a new account to the database.
    # Make sure password is encrypted!!
    # returns 0 if successful, -1 if the username already exists"""
    new_acc = Account(username=username, password=password, comics="", characters="")
    test_acc = Account.query.filter_by(username=username).first()
    if test_acc is not None:
        if test_acc.username == username:
            return -1
    db.session.add(new_acc)
    db.session.commit()
    return 0


def remove_comic(uid, comic_id):
    """
    # removes comic from the comics entry for the given user
    # returns 0 if successful, -1 if the comic could not be found"""
    comics = decode_string(get_account_db_comics(uid))
    if comics.count(comic_id) == 0:
        return -1
    comics.remove(comic_id)
    get_account_db_entry(uid).comics = encode_string(comics)
    db.session.commit()
    return 0


def remove_character(uid, character_id):
    """# removes character from the characters entry for the given user
    # returns 0 if successful, -1 if the entry could not be found"""
    local_characters = decode_string(get_account_db_characters(uid))
    if local_characters.count(character_id) == 0:
        return -1
    local_characters.remove(character_id)
    get_account_db_entry(uid).characters = encode_string(local_characters)
    db.session.commit()
    return 0


def add_comic(uid, comic_id):
    """# adds comic from the comics entry for the given user
    # returns 0 if successful,
    # -1 if the entry could not be added because the max has been reached, and -2 if the entry is already present"""
    comics = decode_string(get_account_db_comics(uid))
    if len(comics) >= 20:
        return -1
    if comics.count(comic_id) > 0:
        return -2
    comics.append(comic_id)
    get_account_db_entry(uid).comics = encode_string(comics)
    db.session.commit()
    return 0


def add_character(uid, character_id):
    """# adds character from the character entry for the given user
    # returns 0 if successful, -1 if the entry could not be added
    # because the max has been reached, and -2 if the entry is already present"""
    local_characters = decode_string(get_account_db_characters(uid))

    if len(local_characters) >= 20:
        return -1
    if local_characters.count(character_id) > 0:
        return -2
    local_characters.append(character_id)
    get_account_db_entry(uid).characters = encode_string(local_characters)
    db.session.commit()
    return 0


def decode_string(encoded_string):
    """# decodes a string, returning the encoded list of ids
    # return value of None means that the encoded string is invalid somehow"""
    if encoded_string == "":
        return []
    id_list = encoded_string.split(";")
    # verification tests:
    for ind_id in id_list:
        # no id should be empty
        if len(ind_id) == 0:
            return None
        # all chars should be numbers
        if not ind_id.isdecimal():
            return None
    return id_list


def get_character(uid, character_index):
    """# returns the character at the given index"""
    this_characters = decode_string(get_account_db_characters(uid))
    return this_characters[character_index]


def get_comic(uid, comic_index):
    """# returns the comci at the given index"""
    comics = decode_string(get_account_db_comics(uid))
    return comics[comic_index]


def encode_string(id_list):
    """# encodes a string for storage in the database"""
    ids_str = ""
    for this_id in id_list:
        if len(ids_str) != 0:
            ids_str += ";"
        ids_str += this_id
    return ids_str


def uid_by_username(username):
    """# returns the UID of the given username.
    # returns -1 if the username doesn't exist in the database."""
    acc = Account.query.filter_by(username=username).first()
    if acc is None:
        return -1
    else:
        return acc.uid


def get_account_db_entry(uid):
    """# returns the account object associated with the given UID"""
    acc = Account.query.filter_by(uid=uid).first()
    return acc


def get_account_db_comics(uid):
    """# returns the stored comics, will need to be decoded"""
    return get_account_db_entry(uid).comics


def get_account_db_characters(uid):
    """# returns the stored characters, will need to be decoded"""
    return get_account_db_entry(uid).characters


@app.route("/logout")
@login_required
def logout():
    """logout"""
    flask_login.logout_user()
    return flask.render_template("logout.html")


@app.route("/search", methods=["POST", "GET"])
def search():
    if flask.request.method == "GET":
        return flask.render_template("search.html")
    if flask.request.method == "POST":
        search = flask.request.form["search"]
        offset = flask.request.form["offset"]
        if search == "":
            flask.flash("Bad search parameters, please try again!")
            return flask.render_template(
                "search.html",
                titles=[],
                imgLinks=[],
                creators=[],
                onSaleDates=[],
                buyLinks=[],
            )
        elif marvel.getComicByTitle(search, offset) != False:
            (title, creatorList, onSaleDate, img, buyLink) = marvel.getComicByTitle(
                search, offset
            )

    if not title:
        flask.flash(
            "Either bad search parameters or Marvel API is down. Please try again later."
        )
        return flask.render_template(
            "search.html",
            titles=[],
            imgLinks=[],
            creators=[],
            onSaleDates=[],
            buyLinks=[],
        )
    return flask.render_template(
        "search.html",
        titles=title,
        imgLinks=img,
        creators=creatorList,
        onSaleDates=onSaleDate,
        buyLinks=buyLink,
    )
    # else:
    #     pass
    #     flask.flash("Bad search parameters, please try again!")
    #     return flask.render_template(
    #         "search.html",
    #         titles=[],
    #         imgLinks=[],
    #         creators=[],
    #         onSaleDates=[],
    #         buyLinks=[],
    #     )
    #     flask.flash(
    #         "The API service may be down. Please try again at a later date!"
    #     )
    #     return flask.render_template(
    #         "search.html",
    #         titles=[],
    #         imgLinks=[],
    #         creators=[],
    #         onSaleDates=[],
    #     )


@app.route("/filter", methods=["POST"])
def setFilter():
    """set filter"""
    choice = flask.request.form["option"]
    return flask.redirect(flask.url_for("search", choice=choice))


@app.route("/")
def index():
    """index"""
    return flask.render_template("index.html")


@app.route("/signup")
def signup():
    """signup"""
    return flask.render_template("signup.html")


@app.route("/signup", methods=["POST"])
def register():
    """register"""
    username = flask.request.form.get("username")
    password = encrypt(flask.request.form.get("password"))
    if add_account(username, password) == -1:
        flask.flash("That username is taken!")
        return flask.redirect("/signup")
    else:
        add_account(username, password)
        flask.flash("Successful signup!")
    return flask.redirect("/login")


@app.route("/quiz")
def quiz():
    """quiz"""
    return flask.render_template("quiz.html")


@app.route("/login", methods=["POST", "GET"])
def sign_in():
    """sing_in"""
    if flask.request.method == "POST":
        username = flask.request.form.get("username")
        password = flask.request.form.get("password")
        user = Account.query.filter_by(username=username).first()
        if user:
            if password == decrypt(user.password):
                user.authenticated = True
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


@app.route("/characterinfo", methods=["POST", "GET"])
def characterinfo():
    return flask.render_template("characterInfo.html")


@app.route("/setfav")
def setfav():
    """# sets favorite character in a redirect, because there are multiple forms and it gets weird"""
    cookies = flask.request.cookies
    cindex = cookies.get("cindex")
    if cindex:  # if the needed cookie exists
        if cindex != "":
            # add cid to user favorites
            user = current_user.get_id()
            res = None
            if user:
                ret = add_character(user, cindex)
                print("Added character return code : " + str(ret))
                res = flask.render_template("favorite_success.html")
            else:
                print("favorite failure!")
                res = flask.render_template("favorite_fail.html")
            resp = flask.make_response(res)
            resp.set_cookie("cindex", "", expires=0)  # clear the now un-needed cookie
            return resp
    return flask.render_template("index.html")


@app.route("/characters", methods=["POST", "GET"])
def characters():
    """# does NOT handle favorites for the characters, that is sent to
    # /setfav because multiple forms
    # this is done by making the favorite button assign a
    # cookie and redirecting to /setfav,
    # because that is somehow the easiest way to do this"""
    if flask.request.method == "GET":
        return flask.render_template("characters.html")
    if flask.request.method == "POST":
        # search bar
        local_search = flask.request.form["search"]
        if local_search == "":
            flask.flash("Bad search parameters, please try again!")
            return flask.render_template(
                "characters.html", titles=[], imgLinks=[], descriptions=[]
            )

        (ids, name, description, imgLink) = marvel.getCharacter(local_search, 0)

        if ids:
            return flask.render_template(
                "characters.html",
                titles=name,
                imgLinks=imgLink,
                descriptions=description,
                ids=ids,
            )
        # searchbar failure
        flask.flash(
            "Either bad search parameters or Marvel API is down. Please try again later."
        )
        return flask.render_template(
            "characters.html", titles=[], imgLinks=[], descriptions=[]
        )


@app.route("/comicinfo", methods=["POST", "GET"])
@app.route("/comicInfo", methods=["POST", "GET"])
def comicinfo():
    """# both app routes because both are referenced and it's best not to rock the boat for now"""
    if flask.request.method == "GET":
        return flask.render_template("comicInfo.html")
    if flask.request.method == "POST":
        # post occurs when the favorite button is pushed.
        cookies = flask.request.cookies
        cid = ""
        for (
            i
        ) in (
            flask.request.cookies
        ):  # first cookie that isn't one of the corrowing known cookies,
            # because for some reason we encode the data in the name
            # of the cookie lol
            if i != "" and i != "session" and i != "id" and i != "cindex":
                cid = i
                break
        cid = cid.split("|").pop().split("/")[5]  # get the encoded data
        user = current_user.get_id()
        if user:  # if the user exists, add the comic to their favorites
            add_comic(user, cid)
            return flask.render_template("favorite_success.html")
        else:
            return flask.render_template("favorite_fail.html")


@app.route("/about")
def about():
    """abougt page"""
    return flask.render_template("landingPage.html")


@app.route("/comicInfo", methods=["POST", "GET"])
def comicInfo():
    """comic info page"""
    return flask.render_template("comicInfo.html")


@app.route("/characterInfo", methods=["POST", "GET"])
def characterInfo():
    """character info"""
    return flask.render_template("characters.html")


def init_profile():
    """parse db data"""
    comics = decode_string(get_account_db_comics(flask_login.current_user.uid))
    titles = []
    creators = []
    imgs = []
    links = []
    for comic_id in comics:
        if marvel.getComicById(comic_id):
            (title, creatorList, onSaleDate, img, buyLink) = marvel.getComicById(
                comic_id
            )
            titles.append(title)
            creators.append(creatorList)
            imgs.append(img)
            links.append(buyLink)
    args = [titles, creators, imgs, links]
    return args


def init_profile2():
    """helper function"""
    local_characters = decode_string(
        get_account_db_characters(flask_login.current_user.uid)
    )
    names = []
    descriptions = []
    imgs = []
    for character_id in local_characters:
        if marvel.getCharacterById(character_id):
            (name, description, imgLinks) = marvel.getCharacterById(character_id)
            names.append(name)
            descriptions.append(description)
            imgs.append(imgLinks)
    args = [names, descriptions, imgs]
    return args


@app.route("/profile", methods=["POST", "GET"])
def profile():
    """faovrites page"""
    comics = init_profile()
    this_characters = init_profile2()
    return flask.render_template(
        "profile.html",
        test="test",
        username=flask_login.current_user.username,
        fav_chars=decode_string(
            get_account_db_characters(flask_login.current_user.uid)
        ),
        fav_comics=decode_string(get_account_db_comics(flask_login.current_user.uid)),
        titles=comics[0],
        creators=comics[1],
        imgs=comics[2],
        links=comics[3],
        name=this_characters[0],
        description=this_characters[1],
        charImg=this_characters[2],
    )


app.run(host="0.0.0.0", port=os.getenv("PORT", 8080), use_reloader=True)
