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


basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_CODE_FOLDER = os.path.join(basedir, 'static/default/code')

db = SQLAlchemy()
app = Flask(__name__)


app.config['UPLOAD_CODE_FOLDER'] = UPLOAD_CODE_FOLDER

app.config["MONGO_URI"] = 'mongodb+srv://alhassanmumin8:Mumin2121@cluster0.tmjnuoz.mongodb.net/video_names?retryWrites=true&w=majority'
mongo = PyMongo(app)


# for encryption of password
bcrypt = Bcrypt(app)


migrate = Migrate(app, db)


app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///mydb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# app.permanent_session_lifetime = timedelta(minutes=60)
# the csrf attack
app.config['SECRET_KEY'] = os.urandom(24)
csrf = CSRFProtect(app)


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'masschusse@gmail.com'
app.config['MAIL_PASSWORD'] = 'wgnmflqcikprmseo'

mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# login_manager.needs_refresh_message = 'Please log in again.'
login_manager.needs_refresh_message_category = 'danger'
login_manager.login_message = u'please login first'
