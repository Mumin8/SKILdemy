from flask import Blueprint, render_template

home_bp = Blueprint('Home', __name__, static_folder='static', template_folder='templates')


@home_bp.route('/')
def home():
    """_summary_
    """
    return render_template("home/home.html")
