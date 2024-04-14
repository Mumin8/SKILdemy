from flask import Blueprint, render_template
from learning_platform.models.models import Course

home_bp = Blueprint('home', __name__, static_folder='static',
                    template_folder='templates')


@home_bp.route('/')
def home():
    '''
    home:
        the page visited when the site is visited 
    '''
    # print(f'the environment variable: {type(os.getenv("AWS_ACCESS_KEY_ID"))}')
    courses = Course.query.all()
    return render_template('home/home.html', courses=courses)

# @app.route('/<int:course_id>/', methods=["GET"])
# def home_(course_id):
#     '''
#     home:
#         the page visited when a course is clicked
#     '''
#     course = Course.query.get(course_id)
#     topics = Course.query.get(course_id).topics

#     return render_template('Home/home_page.html', topics=topics, course=course)
