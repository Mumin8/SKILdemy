from flask import Flask
from dotenv import load_dotenv
from flask_babel import Babel
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_pymongo import PyMongo
from flask_wtf.csrf import CSRFProtect
import os, sys
from learning_platform.google_translations import get_locale


abs_pkg_path = os.path.dirname(sys.modules['learning_platform'].__file__)
pkg_path = os.path.join(abs_pkg_path, "translations")


basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_CODE_FOLDER = os.path.join(basedir, 'static/default/code')

load_dotenv()

db = SQLAlchemy()
app = Flask(__name__)

babel = Babel(app, locale_selector=get_locale, default_locale='en')
app.config['BABEL_TRANSLATION_DIRECTORIES'] = pkg_path

app.config['UPLOAD_CODE_FOLDER'] = UPLOAD_CODE_FOLDER


limiter = Limiter(get_remote_address, 
                  app=app, 
                  default_limits=['7 per second'],
                  storage_uri="memory://")

app.config["MONGO_URI"] = 'mongodb+srv://alhassanmumin8:Mumin2121@cluster0.tmjnuoz.mongodb.net/video_names?retryWrites=true&w=majority'
mongo = PyMongo(app)


# r = redis.StrictRedis(host='localhost', port=6379, db=0)


# for encryption of password
bcrypt = Bcrypt(app)


migrate = Migrate(app, db, render_as_batch=True)



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
# app.config['MAIL_USERNAME'] = 'masschusse@gmail.com'
# app.config['MAIL_PASSWORD'] = 'wgnmflqcikprmseo'

# app.config['MAIL_USERNAME'] = 'skildemymailreset@gmail.com'
# app.config['MAIL_PASSWORD'] = 'qbhukbawmcxpncum'

app.config['MAIL_USERNAME'] = 'skildemycontact@gmail.com'
app.config['MAIL_PASSWORD'] = 'alfppmgjnsrbpzwl'

mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.needs_refresh_message_category = 'danger'
login_manager.login_message = u'please login first'
