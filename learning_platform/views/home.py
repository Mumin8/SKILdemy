from flask import Blueprint, render_template, session
from flask_babel import gettext
from flask_login import current_user
from learning_platform import db
from learning_platform.google_translations import text_translator
from learning_platform.models.models import Course
from learning_platform._helpers import exchange_rate, time_, get_lang, auth_,free_trial, encryption

home_bp = Blueprint(
    'home',
    __name__,
    static_folder='static',
    template_folder='templates')


@home_bp.route('/')
def home():
    '''the page visited when the site is visited
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

    auth = auth_()
    lang = get_lang()
    if lang == None:
        lang = 'en'
    lang = lang + '.jpg'
   
    return render_template(
        'home/home.html',
        courses=courses,
        auth=auth, lang=lang, welc=welc)


@home_bp.route('/<string:course_id>/', methods=["GET"])
def home_(course_id):
    '''the page visited when a course is clicked'''
    auth = auth_()
    lang = get_lang()
    if lang == None:
        lang =  'en'
    lang = f'{lang}.jpg'
    course = Course.query.get(course_id)
    
    if course is not None:
        desc = course.description
        if get_lang() != 'en':
            desc = text_translator(desc, get_lang())  
        trial = course.trial_topics
        free = free_trial(trial)
        topics = course.topics
        return render_template(
            'home/home.html',
            desc=desc,
            tr=free,
            topics=topics,
            course=course,
            lang=lang,
            auth=auth)
    return render_template(
        'home/home.html',
        course=course,
        lang=lang,
        auth=auth)
