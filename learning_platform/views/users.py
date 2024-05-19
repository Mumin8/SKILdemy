import os
import urllib.request
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, send_from_directory
# from learning_platform.google_translations import _translator, from_eng_to_others
from flask_login import login_required, current_user, logout_user, login_user
from flask_mail import Message
from learning_platform import bcrypt, db, app, mail
from learning_platform.forms.form import Registration, LoginForm, ResetForm, NewPasswordForm
from learning_platform.models.models import User, Course, SubTopic, TimeTask, YouTube
from learning_platform._helpers import (
    c_and_topics,
    read_content,
    copy_ai_video,
    validate_time_task,
    user_courses,
    get_ref,
    vid_ids,
    verify_payment,
    completed_course)
from PIL import Image, ImageDraw, ImageFont

user_bp = Blueprint('users', __name__, static_folder='static',
                    template_folder='templates')


ref = []


def pop_ref():
    for i, v in enumerate(ref):
        ref.pop(i)


def user_enrolled_courses(course_id):
    if current_user.is_authenticated:
        # user = User.query.get(current_user.id)
        for c in current_user.enrolling:
            if c.id == course_id:
                return True
        return False

    flash('please login first', category='info')
    return redirect(url_for('home.home'))


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
            if user and bcrypt.check_password_hash(
                    user.password, form.password.data):
                user.authenticated = True
                db.session.add(user)
                db.session.commit()
                login_user(user)
                next = request.args.get(
                    'next_url') or url_for('users.userprofile')
                flash('Happy Coding!  😊', category='success')
                return redirect(next)
            flash("Invalid Credentials", category='warning')
            return redirect(url_for('users.login'))
        except BaseException:
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
    return redirect(url_for('home.home'))


@user_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ResetForm()
    if form.validate_on_submit():
        email = form.email.data
        # check if password exists in the database first
        user = User.query.filter_by(email=email).first()
        if user:
            token = get_ref()
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
    return render_template(
        'user/reset_password.html',
        form=form,
        title='Reset Password')


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


@user_bp.route('/enrol/<string:course_id>', methods=['GET', 'POST'])
@login_required
def enroll_course(course_id):
    '''
    the student will enroll in the course
    '''
    # this will be used in admin to know the number of users for a particular course
    # course_enrollers(course_id)

    # user = User.query.get(current_user.id)

    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    status, result = verify_payment(ref[0])

    if status:
        course = Course.query.get(course_id)

        price = course.price
        rate = course.rate
        if result['amount'] > rate * price * 65:
            course.update_enrolled_at(datetime.now())
            current_user.enrolling.append(course)
            db.session.commit()
            flash(
                f'You have successfully enrolled in {course.name}',
                category='info')
            return render_template('payment/success.html')
    else:
        flash(
            f'unsuccessful, please check your details or contact paystack support',
            category='info')
        return render_template('payment/unsuccessful.html')


@user_bp.route("/userprofile", methods=['GET', 'POST'])
def userprofile():
    '''
    userprofile:
        this will initiate the user profile setting
    '''
    if current_user.is_authenticated:
        user = User.query.filter_by(id=current_user.id).first()
        return render_template(
            'user/profile.html',
            user_courses=user.enrolling)
    next_url = request.url
    print(f'the userprofile next: {next_url}')
    return redirect(url_for('home.home', next_url=next_url))


@user_bp.route('/learns/<string:course_id>/', methods=['GET', 'POST'])
def learn_skills(course_id):
    '''
    the course and topics will be displayed for the
    '''
    if not current_user.is_authenticated:
        next_url = request.url
        print(f'the learn skill next: {next_url}')
        return redirect(url_for('users.login', next_url=next_url))

    user_c = Course.query.get(course_id)
    if user_c:
        c_and_t = c_and_topics(user_c)
        first_key, first_value = next(iter(c_and_t.items()))
        return render_template(
            'user/learn_page.html',
            fk=first_key,
            fv=first_value)
    return render_template('user/learn_page.html')


@user_bp.route('/request/<string:topic_id>', methods=['GET', 'POST'])
def request_task_solution(topic_id):
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))
    usertask = TimeTask.query.get(topic_id)
    user = User.query.get(current_user.id)
    user.time_task.append(usertask)
    db.session.commit()
    flash('successfully associate timely task for your request')
    return 'added to time tasks'


@user_bp.route('/mat/<string:course_id>/<string:topic_id>',
               methods=['GET', 'POST'])
def topic_by_course(course_id, topic_id):
    '''
    gets and displays the reading content for the user
    '''
    course = Course.query.get(course_id).name
    topic = SubTopic.query.get(topic_id).name
    if course:
        mat = read_content(course, topic)
    return render_template(
        'user/learn_page.html',
        mat=mat,
        course_id=course_id,
        topic_id=topic_id)


@user_bp.route('/gptplus_vid/<string:course_id>/<string:topic_id>',
               methods=['GET', 'POST'])
@login_required
def gptplus_vid(course_id, topic_id):
    '''
    gptplus_vid:
        this will get the video here straight away
    '''
    course = Course.query.get(course_id).name
    topic = SubTopic.query.get(topic_id).name
    file = f'{course}_{topic}.mp4'

    if not current_user.is_authenticated:
        return redirect(url_for('users.logn'))

    status, state = validate_time_task(current_user.id, topic_id, topic)
    if status and state == "Not timely":
        vid_path = os.path.join(app.static_folder, 'myvideo', file)
        dest_path = os.path.join(app.static_folder, 'user_output')

        name = copy_ai_video(vid_path, dest_path)
        not_time = state
        return render_template(
            'user/learn_page.html',
            path=name,
            course_id=course_id,
            not_time=not_time)

    elif not status and state == "pending":
        name = "not yet ready"
        pending = state
        return render_template(
            'user/learn_page.html',
            path=name,
            course_id=course_id,
            topic_id=topic_id,
            pending=pending)
    elif not status and state == 'request':
        name = "make request"
        ask = state
        flash('You can request for the solution')
        return render_template(
            'user/learn_page.html',
            path=name,
            course_id=course_id,
            topic_id=topic_id,
            ask=ask)


@user_bp.route('/payment/<string:course_id>', methods=['GET'])
def make_payment(course_id):
    '''
        This is where payment is made
    '''
    stat = user_enrolled_courses(course_id)
    if stat:
        flash('Already enrolled, login and start learning', category='info')
        return redirect(url_for('home.home'))

    if not current_user.is_authenticated:
        next_url = request.url
        print(f'the next url: {next}')
        return redirect(url_for('users.login', next_url=next_url))

    user = User.query.get(current_user.id)
    email = user.email

    course = Course.query.get(course_id)
    rate = course.rate
    price = course.price
    amount = rate * price * 100
    _price = price
    c_id = course.id
    c_name = course.name

    pop_ref()

    ref.append(get_ref())

    pk = os.getenv("PAYSTACK_PUBLIC_KEY")
    return render_template(
        'payment/payment.html',
        c_id=c_id,
        _price=_price,
        amount=amount,
        c_name=c_name,
        email=email,
        pk=pk,
        ref=ref[0])


@user_bp.route('/yt_vid/<string:topic_id>', methods=['GET', 'POST'])
def youtube_vids(topic_id):
    '''
    this will get the video related to the topic in youtube
    '''
    subtopic = SubTopic.query.filter_by(id=topic_id).first()
    subtopic_videos = subtopic.youtube_videos
    vids = vid_ids(subtopic_videos)

    return render_template('user/watch_youtube_video.html', paths=vids)


@user_bp.route('/locale', methods=['GET', 'POST'])
def user_locale():
    '''
    this will get the language of the client user
    '''
    if request.method == "POST":
        session['lang'] = request.form.get('language')
        return redirect(url_for('home.home'))

    return render_template('user/locale.html')


@user_bp.route('/cert/<string:course_id>', methods=['GET', 'POST'])
def cert_of_completion(course_id):
    '''
    where the certificate will be initiated
    '''

    if not current_user.is_authenticated:
        next_url = request.url
        print(f'the next url: {next}')
        return redirect(url_for('users.login', next_url=next_url))

    course = Course.query.get(course_id)

    for c in current_user.enrolling:
        if c == course:
            if completed_course(c):
                flash(
                    'Your certificate is ready for download',
                    category='info')
                return render_template(
                    'user/certificate.html', course_id=c.id, name=c.name)
            else:
                flash(
                    "certificate will be ready after completion",
                    category='info')
                return redirect(url_for('users.userprofile'))
    return redirect(url_for('users.userprofile'))


@user_bp.route('/preview_cert/<string:course_id>', methods=['GET', 'POST'])
def download_cert(course_id):

    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    course = Course.query.get(course_id)
    root_path = app.root_path
    src = 'certificate.jpg'
    dest = current_user.id + '.jpg'

    source_path = os.path.join(root_path, 'static', 'certificate', src)
    dest_path = os.path.join(root_path, 'static', 'student_certificates', dest)
    resize = (1056, 816)
    img = Image.open(source_path)
    img = img.resize(resize)
    img = img.convert('RGB')
    original_size = img.size

    print(f'the original size {original_size}')

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('arial.ttf', 32)

    student_name_pos = (218, 410)
    course_name_pos = (218, 514)
    completed_date_pos = (670, 612)

    student_name = current_user.fullname
    course_name = course.name
    for c in current_user.enrolling:
        if c == course:
            completed_on = c.enrolled_at + timedelta(days=120)
            completed_on, _ = str(completed_on).split()
            break

    draw.text(student_name_pos, student_name, font=font)
    draw.text(course_name_pos, course_name, font=font)
    draw.text(completed_date_pos, completed_on, font=font)

    img.save(dest_path)

    return render_template('user/view_cert.html', dest=dest)


@user_bp.route('/dl_cert', methods=['GET', 'POST'])
def download_your_cert():
    '''
    where the certificate will be downloaded
    '''
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    root_path = app.root_path
    cert = current_user.id + '.jpg'
    cert_path = os.path.join(root_path, 'static', 'student_certificates')
    name = 'certificate.jpg'

    return send_from_directory(
        cert_path,
        cert,
        as_attachment=True,
        download_name=name)
