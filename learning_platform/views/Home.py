from flask import Blueprint, render_template, session
from flask_babel import gettext
from flask_login import current_user
from learning_platform import db
from learning_platform.models.models import Course
from learning_platform.google_translations import get_locale
from learning_platform._helpers import exchange_rate, time_, get_lang, _auth

home_bp = Blueprint(
    'home',
    __name__,
    static_folder='static',
    template_folder='templates')


welcome_message = {
    'ar': 'Arabic stuff',
    'bn': 'Bengali stuff',
    'zh-CN': 'Chinese stuff',
    'en': 'English stuff',
    'es': 'Spanish stuff',
    'fr': 'French stuff',
    'hi': 'Hindi stuff',
    'id': 'Indonesia stuff',
    'pt': 'Portuguese stuff',
    'ru': 'Russian stuff',
    'tr': 'Turkish stuff',
    'ur': 'Urdu stuff'
}


@home_bp.route('/')
def home():
    '''
    home:
        the page visited when the site is visited
    '''

    welc = gettext('Welcome to SKILdemy')

    courses = Course.query.all()

    status, t = time_()
    if status:
        rate = exchange_rate()

        for c in courses:
            c.update(t)
            c.rate = rate
        db.session.commit()

    auth = _auth()

    # for getting locale flag
    lang = get_lang()
    lang = lang + '.jpg'

    return render_template(
        'home/home.html',
        courses=courses,
        auth=auth, lang=lang, welc=welc)


@home_bp.route('/<string:course_id>/', methods=["GET"])
def home_(course_id):
    '''
    home:
        the page visited when a course is clicked
    '''

    auth = _auth()
    lang = get_lang()
    lang = lang + '.jpg'
    
    course = Course.query.get(course_id)

    if course is not None:

        topics = course.topics
        return render_template('home/home.html', topics=topics, course=course, lang=lang, auth=auth)
    return render_template('home/home.html', course=course, lang=lang, auth=auth)
