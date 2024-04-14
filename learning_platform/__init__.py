from flask import Flask
from datetime import timedelta
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_pymongo import PyMongo
from flask_wtf.csrf import CSRFProtect
import os


db = SQLAlchemy()
app = Flask(__name__)

app.config["MONGO_URI"] = os.getenv("MONGODB_URI")
mongo = PyMongo(app)


# for encryption of password
bcrypt = Bcrypt(app)


app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///mydb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# app.permanent_session_lifetime = timedelta(minutes=60)
# the csrf attack
app.config['SECRET_KEY'] = os.urandom(24)
csrf = CSRFProtect(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# login_manager.needs_refresh_message = 'Please log in again.'
login_manager.needs_refresh_message_category = 'danger'
login_manager.login_message = u'please login first'
