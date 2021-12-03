"""this is the testing file"""
import os
import unittest
import flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from dotenv import find_dotenv, load_dotenv
from cryptography.fernet import Fernet
from flask_login import LoginManager

from app import remove_comic, remove_character, add_comic, add_character

app = flask.Flask(__name__)
app.secret_key = "this is the most secretive key in the universe!!!"

login_manager = LoginManager()
login_manager.init_app(app)


load_dotenv(find_dotenv())


CRYPTOGRAPHY_KEY = os.getenv("CRYPTO_KEY").encode("UTF-8")
encryption_engine = Fernet(CRYPTOGRAPHY_KEY)
# database location

engine = create_engine(
    "postgresql://hxbfjmfvfojzkv:f307f9122a40563211c43b4bbbf03e8ac9e8e2d3c0525aa3b1b4"
    "62ee2ca48810@ec2-23-23-133-10.compute-1.amazonaws.com:5432/d9nffekjuq21dl"
)


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
    """db table schema"""
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    comics = db.Column(db.String(200), nullable=False)
    characters = db.Column(db.String(200), nullable=False)

    # Login stuff
    authenticated = False

    def is_active(self):
        """check if active"""
        return True

    def get_id(self):
        """get uid"""
        return self.uid

    def is_authenticated(self):
        """get authentication status"""
        return self.authenticated

    def is_anonymous(self):
        """check if user is anonymous"""
        return False


db.create_all()
db.session.commit()

print(Account.query.with_entities(Account.characters).filter(Account.uid == 1).one())


class GetURLTestCase(unittest.TestCase):
    """all test cases"""
    #########comic testing##########
    def test_a_add_multi_comic(self):
        """test case for adding multiple comics"""
        add_comic(1, '1234')
        add_comic(1, '9876')
        user_comics = Account.query.with_entities(Account.comics).filter(Account.uid == 1).one()
        self.assertEqual(user_comics[0], '1234;9876', 'Multi Add Comic Failed')

    def test_b_add_dupe_comic(self):
        """test case for adding duplicate comic"""
        add_comic(1, '1234')
        user_comics = Account.query.with_entities(Account.comics).filter(Account.uid == 1).one()
        self.assertEqual(user_comics[0], '1234;9876', 'Duplicate Add Comic Failed')

    def test_c_remove_comic(self):
        """test case for deleting single comic"""
        remove_comic(1, '1234')
        user_comics = Account.query.with_entities(Account.comics).filter(Account.uid == 1).one()
        self.assertEqual(user_comics[0], '9876', 'Remove Single Comic Failed')

    def test_d_add_del_comic(self):
        """test case for adding and deleting comics"""
        add_comic(1, '1111')
        remove_comic(1, '9876')
        remove_comic(1, '1111')
        user_comics = Account.query.with_entities(Account.comics).filter(Account.uid == 1).one()
        self.assertEqual(user_comics[0], '', 'Compound Operation Comic Failed')

#########character testing##########
    def test_e_add_multi_character(self):
        """test case for adding multiple characters"""
        add_character(1, '1234')
        add_character(1, '9876')
        user_chars = Account.query.with_entities(Account.characters).filter(Account.uid == 1).one()
        self.assertEqual(user_chars[0], '1234;9876', 'Multi Add Character Failed')

    def test_f_add_dupe_character(self):
        """test case for adding duplicate character"""
        add_character(1, '1234')
        user_chars = Account.query.with_entities(Account.characters).filter(Account.uid == 1).one()
        self.assertEqual(user_chars[0], '1234;9876', 'Duplicate Add Character Failed')

    def test_g_remove_character(self):
        """test case for remove single character"""
        remove_character(1, '1234')
        user_chars = Account.query.with_entities(Account.characters).filter(Account.uid == 1).one()
        self.assertEqual(user_chars[0], '9876', 'Remove Single Character Failed')

    def test_h_add_del_character(self):
        """test case for adding and deleting characters"""
        add_character(1, '1111')
        remove_character(1, '9876')
        remove_character(1, '1111')
        user_chars = Account.query.with_entities(Account.characters).filter(Account.uid == 1).one()
        self.assertEqual(user_chars[0], '', 'Compound Operation Character Failed')


if __name__ == "__main__":
    unittest.main()
