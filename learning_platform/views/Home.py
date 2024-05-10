from flask import Blueprint, render_template
from learning_platform.models.models import Course
from learning_platform.google_translations import get_locale
home_bp = Blueprint('home', __name__, static_folder='static',
                    template_folder='templates')


welcome_message = {'ar': 'Arabic stuff', 'bn': 'Bengali stuff', 'zh-CN': 'Chinese stuff',
                   'en': 'English stuff', 'es': 'Spanish stuff', 'fr': 'French stuff',
                    'hi': 'Hindi stuff', 'pt': 'Portuguese stuff', 'ru': 'Russian stuff',
                     'tr': 'Turkish stuff', 'ur': 'Urdu stuff'}

@home_bp.route('/')
def home():
    '''
    home:
        the page visited when the site is visited 
    '''
    
    user_locale = get_locale()
    courses = Course.query.all()
    return render_template('home/home.html', courses=courses, welcome=welcome_message[user_locale])

# @app.route('/<int:course_id>/', methods=["GET"])
# def home_(course_id):
#     '''
#     home:
#         the page visited when a course is clicked
#     '''
#     course = Course.query.get(course_id)
#     topics = Course.query.get(course_id).topics

#     return render_template('Home/home_page.html', topics=topics, course=course)
