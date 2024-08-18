import os
from datetime import datetime, timedelta
import requests
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    jsonify,
    flash,
    session)
from botocore.exceptions import ClientError
from flask_babel import gettext as _
from flask_limiter.errors import RateLimitExceeded
from flask_login import login_required, current_user, logout_user, login_user
from flask_mail import Message
from learning_platform import bcrypt, db, app, mail, limiter
from learning_platform.forms.form import Registration, LoginForm, ResetForm, NewPasswordForm
from learning_platform.models.models import User, Course, SubTopic, TimeTask
from learning_platform.google_translations import text_translator
from learning_platform._helpers import (
    c_and_topics,
    cached,
    task_pending,
    free_trial,
    validate_time_task,
    get_ref,
    get_lang,
    presigned_url,
    presigned_cert_url,
    upload_certificate,
    s3_client,
    encryption,
    verify_payment,
    completed_course)
from PIL import Image, ImageDraw, ImageFont

user_bp = Blueprint('users', __name__, static_folder='static',
                    template_folder='templates')


ref = []


def cert_available(key):
    s3 = s3_client()
    cert = f'{encryption("cert")[:16]}'
    try:
        s3.get_object(Bucket=cert, Key=key)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return False
    return True


def pop_ref():
    for i, v in enumerate(ref):
        ref.pop(i)


def user_enrolled_courses(course_id):
    if not current_user.is_authenticated:
        flash(_('please login first'), category='info')
        return redirect(url_for('home.home'))
    user_courses = current_user.enrolling
    for c in user_courses:
        if c.id == course_id:
            return True, c
    return False, None


def completed_topics(c):
    user = current_user
    all = 0
    some = 0
    for u in c.time_task.sub_topic:
        all += 1
        for t in user.time_task:
            if u.name_a == t.usertask:
                some += 1
                break
    return int((some / all)*100)


@user_bp.errorhandler(RateLimitExceeded)
def rateLimit_handler(e):
    return jsonify(error='something went wrong. try again')


@user_bp.route("/auth")
def register_auth():
    return render_template('user/home_page.html')


@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    l = 'This name will appear on your certificate when you enroll in a course'
    lang = get_lang()
    if lang != "en":
        l = text_translator(l, lang)

    form = Registration(request.form)
    if form.validate_on_submit():
        fullname = form.fullname.data
        username = form.username.data
        email = form.email.data
        moderator = False
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        if current_user.moderator:
            moderator = True
        if not User.query.filter_by(email=email).first():
            user = User(fullname=fullname, username=username, email=email,
                        password=hashed_password, moderator=moderator)
            db.session.add(user)
            db.session.commit()
            if moderator:
                flash(
                    f"you have successfully registered {fullname} as admin",
                    category='success')
            else:
                flash(_("Thank you for Registering"), category='success')
        return redirect(url_for('users.register_auth'))
    return render_template('user/register.html', form=form, l=l)


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
                flash(_('Happy Coding!  😊'), category='success')
                return redirect(next)
            flash(_("Invalid Credentials"), category='warning')
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

        lnk_ms = 'Click this link to reset your password'
        if get_lang() != 'en':
            lnk_ms = text_translator(lnk_ms, get_lang())

        if user:
            token = get_ref()
            user.reset_token = token
            db.session.commit()
            msg = Message(_('Password Reset Request'),
                          sender='skildemycontact@gmail.com',
                          recipients=[email])
            msg.body = f'''
            {lnk_ms}
            {url_for('users.reset_password', token=token, _external=True)}
            '''
            mail.send(msg)

            flash(_('Check your email for the password reset link.'),
                  category='success')
        else:
            flash(_('Email not found'), category='danger')
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
            flash(_('successfully reset password'))
            return redirect(url_for('users.login'))
    return render_template('user/reset_password_confirm.html', form=form)


@user_bp.route('/enrol/<string:course_id>', methods=['GET', 'POST'])
@login_required
def enroll_course(course_id):
    '''
    the student will enroll in the course
    '''

    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    status, result = verify_payment(ref[0])

    if status:
        course = Course.query.get(course_id)

        price = course.price
        rate = course.rate
        if result['amount'] > rate * price * 65:

            mes = _('You have successfully enrolled in', category='success')
            for c in current_user.enrolling:
                if c == course:
                    c.update_enrolled_at(datetime.now())
                    mes = _(
                        'You have successfully updated your course',
                        category='success')
                    break
            else:
                course.update_enrolled_at(datetime.now())
                current_user.enrolling.append(course)
                for subt in course.time_task.sub_topic:
                    det_id = encryption(
                        f'{course.course_creator}{subt.topic_id}{subt.id}')
                    new_task = TimeTask(usertask=subt.name_a, id=det_id)
                    db.session.add(new_task)
            db.session.commit()

            flash(
                f'{mes} {course.name}',
                category='info')
            return render_template('payment/success.html')
    else:
        flash(
            _('unsuccessful, please check your details or contact SKILdemy support'),
            category='info')
        return render_template('payment/unsuccessful.html')


@user_bp.route("/userprofile", methods=['GET', 'POST'])
def userprofile():
    '''
    userprofile:
        this will initiate the user profile setting
    '''
    if current_user.is_authenticated:
        _lis = []
        user_courses = current_user.enrolling
        for c in user_courses:
            st, v = completed_course(c)
            pct = completed_topics(c)
           
            if v >= 0:
                ms = text_translator(str(v) + ' days left', get_lang())
                _lis.append([c, ms, pct])
            else:
                _lis.append([c, ' ', pct])
        
        return render_template(
            'user/profile.html',
            user_courses=_lis)
    next_url = request.url
    return redirect(url_for('home.home', next_url=next_url))


@user_bp.route('/next_page/<int:page>/<int:fp>/<int:lp>',
               methods=['GET', 'POST'])
def paginate(page, fp, lp):
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    fk = session.get('c')
    fv = session.get('dict')

    return render_template(
        'user/learn_page.html',
        fk=fk,
        fv=fv,
        page=str(page),
        fp=fp,
        lp=lp)


@user_bp.route('/learns/<string:course_id>', methods=['GET', 'POST'])
def learn_skills(course_id):
    '''
    the course and topics will be displayed for the
    '''
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    user_c = Course.query.get(course_id)
    for c in current_user.enrolling:
        if c == user_c:
            compl_c, n_ = completed_course(c)
            if compl_c:
                flash(
                    _('Please your time period to access this course has elapsed'),
                    category='warning')
                flash(
                    _('Your can always enroll again'),
                    category='info')
                return redirect(url_for('users.userprofile'))
    if user_c:
        c_and_t = c_and_topics(user_c)
        first_key, first_value = next(iter(c_and_t.items()))
        dict_val = {}
        for i, j in enumerate(first_value):
            dict_val[str(i)] = j

        session['dict'] = dict_val
        session['c'] = first_key
        page = '0'
        first_page = 0
        last_page = len(first_value) - 1
        return render_template(
            'user/learn_page.html',
            fk=first_key,
            fv=dict_val,
            page=page,
            fp=first_page,
            lp=last_page)
    return render_template('user/learn_page.html')


@user_bp.route('/request/<string:topic_id>', methods=['GET', 'POST'])
def request_task_solution(topic_id):
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    status, trash = task_pending(current_user.id)
    if status:
        usertask = TimeTask.query.get(topic_id)
        user = User.query.get(current_user.id)
        user.time_task.append(usertask)
        db.session.commit()
        flash(_('successfully requested for solution'), category='success')
    else:
        flash(_('There is already one task pending for solution'), category='warning')
    return redirect(url_for('users.userprofile'))


@user_bp.route('/trial/<string:course_id>/<string:topic_id>',
               methods=['GET', 'POST'])
def free_test(course_id, topic_id):
    '''
    gets and displays the reading content for the user
    '''
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    course = Course.query.get(course_id)
    topic = SubTopic.query.get(topic_id)
    trial = free_trial(course.trial_topics)
    if topic in trial:
        mat, iframes = cached(course.name, topic)
        return render_template(
            'user/free_trial.html',
            mat=mat,
            path=iframes,
            course_id=course_id,
            topic_id=topic_id)


@user_bp.route('/mat/<string:course_id>/<string:topic_id>',
               methods=['GET', 'POST'])
def topic_by_course(course_id, topic_id):
    '''
    gets and displays the reading content for the user
    '''
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    stat, c = user_enrolled_courses(course_id)
    if not stat:
        flash(_('You have not enrolled in this course'), category='warning')
        return redirect(url_for('home.home'))

    compl_c, n_ = completed_course(c)
    if compl_c:
        flash(_('Your access time has elapsed, you can access your certificate'), category='warning')
        return redirect(url_for('users.userprofile'))

    course = Course.query.get(course_id).name
    topic = SubTopic.query.get(topic_id)
    if course:
        mat, iframes = cached(course, topic)
    return render_template(
        'user/learn_page.html',
        mat=mat,
        path=iframes,
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
    if not current_user.is_authenticated:
        return redirect(url_for('users.logn'))

    course = Course.query.get(course_id)
    topic = SubTopic.query.get(topic_id)
    _file = f'{course.course_creator}{topic.topic_id}{topic.name}'

    file = encryption(_file) + '.mp4'

    status, state = validate_time_task(current_user.id, topic_id, topic.name_a)
    if status and state == "Not timely":
        url = presigned_url(file)
        not_time = state
        return render_template(
            'user/learn_page.html',
            path=url,
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
        flash(_('You can request for the solution'))
        return render_template(
            'user/learn_page.html',
            path=name,
            course_id=course_id,
            topic_id=topic_id,
            ask=ask)


@user_bp.route('/payment/<string:course_id>', methods=['GET'])
def make_payment(course_id):
    '''This is where payment is made'''
    if not current_user.is_authenticated:
        next_url = request.url
        return redirect(url_for('users.login', next_url=next_url))

    stat, c = user_enrolled_courses(course_id)
    if stat:
        compl_c, n_ = completed_course(c)
        if not compl_c:
            flash(
                _('Already enrolled, You can still access this course'),
                category='info')
            return redirect(url_for('home.home'))
        else:
            flash(
                _('Your time expired for this course and you are trying to enroll again'),
                category='info')

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
    '''where the certificate will be previewed'''

    if not current_user.is_authenticated:
        next_url = request.url
        return redirect(url_for('users.login', next_url=next_url))

    cert_name = f'{current_user.id}{course_id}' + ".jpg"

    course = Course.query.get(course_id)

    for c in current_user.enrolling:
        if c == course:
            compl_c, n_ = completed_course(c)
            if compl_c:
                pct = completed_topics(c)
                if pct >= 70:
                    flash(
                        _('Your certificate is ready for download'),
                        category='info')
                    return render_template(
                        'user/certificate.html', course_id=c.id, name=c.name)
                else:
                    flash(
                        _("Your mark is below 70%. You can enroll again to improve your marks"),
                        category='danger')
                    return redirect(url_for('users.userprofile'))

            else:
                if cert_available(cert_name):
                    return render_template(
                        'user/certificate.html', course_id=c.id, name=c.name)
                else:
                    flash(
                        _("The certificate will be ready after you complete the course"),
                        category='info')
                    return redirect(url_for('users.userprofile'))
    return redirect(url_for('users.userprofile'))


@user_bp.route('/preview_cert/<string:course_id>', methods=['GET', 'POST'])
def download_cert(course_id):
    '''certificate will be downloaded here'''

    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    course = Course.query.get(course_id)
    root_path = app.root_path
    src = 'certificate.jpg'
    dest = current_user.id + '.jpg'

    cert_name = f'{current_user.id}{course.id}' + ".jpg"
    url = presigned_cert_url(cert_name)
    if not cert_available(cert_name):
        source_path = os.path.join(root_path, 'static', 'certificate', src)
        dest_path = os.path.join(
            root_path, 'static', 'student_certificates', dest)
        resize = (1056, 816)
        img = Image.open(source_path)
        img = img.resize(resize)
        img = img.convert('RGB')

        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype('arial.ttf', 32)

        student_name_pos = (218, 410)
        course_name_pos = (218, 514)
        completed_date_pos = (670, 612)

        student_name = current_user.fullname
        course_name = course.name
        duration = course.duration
        for c in current_user.enrolling:
            if c == course:
                completed_on = c.enrolled_at + timedelta(minutes=duration)
                completed_on, _ = str(completed_on).split()
                break

        draw.text(student_name_pos, student_name, font=font)
        draw.text(course_name_pos, course_name, font=font)
        draw.text(completed_date_pos, completed_on, font=font)

        img.save(dest_path)

        upload_certificate(dest_path, cert_name)
        os.remove(dest_path)

        return render_template(
            'user/view_cert.html', dest=url, id=course_id)

    return render_template('user/view_cert.html', dest=url, id=course_id)


@user_bp.route('/dl_cert/<string:id>', methods=['GET', 'POST'])
def download_your_cert(id):
    '''where the certificate will be downloaded'''
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    course = Course.query.get(id)
    cert_name = f'{current_user.id}{course.id}' + ".jpg"
    url = presigned_cert_url(cert_name)
    downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    filename = 'certificate.jpg'
    local_file_path = os.path.join(downloads_path, filename)
    r = requests.get(url)
    if r.status_code == 200:
        with open(local_file_path, 'wb') as file:
            file.write(r.content)
            flash(
                _('Certificate has been generated in your downloads folder'),
                category="success")
    return redirect(url_for('users.userprofile'))
