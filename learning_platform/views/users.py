import os
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user, logout_user, login_user
from learning_platform import bcrypt, db, app
from learning_platform.forms.form import Registration, LoginForm, ResetForm, NewPasswordForm
from learning_platform.models.models import User, Course, SubTopic, TimeTask
from learning_platform._helpers import (c_and_topics, read_content, copy_ai_video,
                                        validate_time_task, user_courses)

user_bp = Blueprint('users', __name__, static_folder='static',
                    template_folder='templates')


def user_enrolled_courses(course_id):
    try:
        user = User.query.get(current_user.id)
        for c in current_user.enrolling:
            if c.id == course_id:
                return True
    except AttributeError:
        return {"error": "please login"}


@user_bp.route("/auth")
def register_auth():
    return render_template('user/home_page.html')


@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = Registration(request.form)
    if form.validate_on_submit():
        fullname = form.fullname.data
        username = form.username.data
        email = form.email.data
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        user = User(fullname=fullname, username=username, email=email,
                    password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Thank you for Registering", category='success')
        return redirect(url_for('users.register_auth'))
    return render_template('user/register.html', form=form)


@user_bp.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        try:
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                user.authenticated = True
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash('Happy Coding!  😊', category='success')
                return redirect(url_for('users.userprofile'))
            flash("Invalid Credentials", category='warning')
            return redirect(url_for('users.login'))
        except:
            return redirect(url_for('users.login'))

    return render_template('user/login.html', form=form)


@user_bp.route("/logout", methods=['GET', 'POST'])
@login_required
def user_logout():
    '''
    user_logout:
        the user will log out from here
    '''
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return redirect(url_for('users.register_auth'))


@user_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ResetForm()
    if form.validate_on_submit():
        email = form.email.data
        # check if password exists in the database first
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token()
            user.reset_token = token
            db.session.commit()
            msg = Message('Password Reset Request',
                          'masschusse@gmail.com', recipients=[email])
            msg.body = f'''
            Click this link to reset your password:
            {url_for('users.reset_password', token=token, _external=True)}
            '''
            mail.send(msg)

            flash('Check your email for the password reset link.',
                  category='success')
        else:
            flash('Email not found', category='danger')
            return redirect(url_for('users.login'))
    return render_template('user/reset_password.html', form=form, title='Reset Password')


@user_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = NewPasswordForm()
    user = User.query.filter_by(reset_token=token).first()
    if user:
        if request.method == 'POST':
            new_password = request.form['password']
            user.set_password(new_password)
            user.reset_token = None
            db.session.commit()
            flash('successfully reset password')
            return redirect(url_for('users.login'))
    return render_template('user/reset_password_confirm.html', form=form)


@user_bp.route('/enrol/<int:course_id>/', methods=['GET', 'POST'])
@login_required
def enroll_course(course_id):
    '''
    the student will enroll in the course
    '''
    # this will be used in admin to know the number of users for a particular course
    # course_enrollers(course_id)
    if user_enrolled_courses(course_id):
        flash('Already enrolled, login and start learning')
        return redirect(url_for('users.login'))
    user = User.query.get(current_user.id)

    course = Course.query.get(course_id)
    current_user.enrolling.append(course)
    db.session.commit()

    flash(f'You have successfully enrolled in {course.name}')
    return "well done"


@user_bp.route("/userprofile", methods=['GET', 'POST'])
@login_required
def userprofile():
    '''
    userprofile:
        this will initiate the user profile setting
    '''

    try:
        user = User.query.filter_by(id=current_user.id).first()
        return render_template('user/profile.html', user=user.enrolling)
    except Exception as e:
        flash('please login')
        return redirect(url_for('users.login'))


@user_bp.route('/learns/<int:course_id>/', methods=['GET', 'POST'])
@login_required
def learn_skills(course_id):
    '''
    the course and topics will be displayed for the
    '''
    user_c = Course.query.get(course_id)
    if user_c:
        c_and_t = c_and_topics(user_c)
        first_key, first_value = next(iter(c_and_t.items()))
        return render_template('user/learn_page.html', fk=first_key, fv=first_value)
    return render_template('user/learn_page.html')


@user_bp.route('/request/<int:topic_id>', methods=['GET', 'POST'])
def request_task_solution(topic_id):
    usertask = TimeTask.query.get(topic_id)
    user = User.query.get(current_user.id)
    user.time_task.append(usertask)
    db.session.commit()
    flash('successfully associate timely task for your request')

    return 'added to time tasks'


@user_bp.route('/mat/<int:course_id>/<int:topic_id>', methods=['GET', 'POST'])
def topic_by_course(course_id, topic_id):
    '''
    gets and displays the reading content for the user
    '''
    course = Course.query.get(course_id).name
    topic = SubTopic.query.get(topic_id).name
    if course:
        mat = read_content(course, topic)
    return render_template('user/learn_page.html', mat=mat, course_id=course_id, topic_id=topic_id)


@user_bp.route('/gptplus_vid/<int:course_id>/<int:topic_id>', methods=['GET', 'POST'])
@login_required
def gptplus_vid(course_id, topic_id):
    '''
    gptplus_vid:
        this will get the video here straight away
    '''
    course = Course.query.get(course_id).name
    topic = SubTopic.query.get(topic_id).name
    file = f'{course}_{topic}.mp4'

    status, state = validate_time_task(current_user.id, topic_id, topic)
    if status and state == "Not timely":
        vid_path = os.path.join(app.static_folder, 'myvideo', file)
        dest_path = os.path.join(app.static_folder, 'user_output')

        name = copy_ai_video(vid_path, dest_path)
        not_time = state
        return render_template('user/learn_page.html', path=name, course_id=course_id, not_time=not_time)

    elif not status and state == "pending":
        name = "not yet ready"
        pending = state
        return render_template('user/learn_page.html', path=name, course_id=course_id, topic_id=topic_id, pending=pending)
    elif not status and state == 'request':
        name = "make request"
        ask = state
        flash('You can request for the solution')
        return render_template('user/learn_page.html', path=name, course_id=course_id, topic_id=topic_id, ask=ask)
