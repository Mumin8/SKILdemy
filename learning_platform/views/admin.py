from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_required, current_user, logout_user, login_user
from learning_platform import bcrypt, db
from learning_platform.forms.form import (
    Registration, LoginForm, CourseForm, TopicForm, SubjectForm, SubTopicForm)
from learning_platform.models.models import User, Video, Course, SubTopic, Subject
from learning_platform._helpers import hash_filename, find_missing_vid

admin_bp = Blueprint(
    'admin', __name__, static_folder='static', template_folder='templates')


@admin_bp.route('/index')
def index():
    approved_videos = Video.query.filter_by(status='approved').all()
    return render_template('admin/index.html', videos=approved_videos)


@admin_bp.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    '''
    admin_login:
        this will log the admin in
    '''
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            user.authenticated = True
            user.moderator = True
            db.session.add(user)
            db.session.commit()
            login_user(user)
            profile_ = user.profile
            if current_user:
                flash('Happy Coding!  😊', category='success')
                return redirect(url_for('admin.index'))
            else:
                flash("login and access this page", category='warning')
                return redirect(url_for('users.login', user_id=user.id))
    return render_template('user/login.html', form=form)



@admin_bp.route('/admin_av', methods=['GET', 'POST'])
def admin_add_vid():
    '''
    admin_add_vid:
        the video to add will be added to session here
    '''
    courses = Course.query.all()
    topics = SubTopic.query.all()
    if request.method == "POST":
        session['course'] = request.form.get('course')
        session['topic'] = request.form.get('topic')
        print(
            f'course {request.form.get("course")} topic {request.form.get("topic")}')
        return redirect(url_for('admin.upload'))
    return render_template('admin/add_video.html', courses=courses, topics=topics)



@admin_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    validate_list()

    course = session.get('course')
    topic = session.get('topic')

    video_ = all_vids()
    v_id.append(video_)

    if len(v_id[0]) > 3:
        flash('the number of videos is up to 4 alread, you will be notified if  a slop is available', category='success')
        return redirect(url_for('learn_skills'))
    else:
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                name = hash_filename(filename)
                _vid = find_missing_vid(v_id[0])
                # file_details = {"video_id": str(_vid), "name": name, "course": course, "topic": topic}
                # file.save(os.path.join(app.config['UPLOAD_FOLDER'], name))
                # online_users = db.python_videos.insert_one(file_details)
                # all_vids()
                return 'it worked'
        return render_template('admin/upload_vid.html')


@admin_bp.route('/reg_course', methods=['GET', 'POST'])
def register_course():
    '''
    register_course:
        this will add a course to the course table
    '''
    form = CourseForm(request.form)
    if form.validate_on_submit():
        name = form.name.data
        desc = form.description.data
        price = form.price.data
        new_course = Course(name=name, description=desc, price=price)
        db.session.add(new_course)
        db.session.commit()
        return jsonify({'message': 'Course created successfully'}), 201
    return render_template('content_management/Register_course.html', form=form)


@admin_bp.route('/cs_avail', methods=['GET', 'POST'])
def cs_avail():
    '''
    cs_avail:
        this will get all the available courses
    '''

    cst = Course.query.all()
    return render_template('admin/index.html', cst=cst)


@admin_bp.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    '''
    add_subject:
        this will add a subject or language to the subject table
    '''
    form = SubjectForm(request.form)
    if form.validate_on_submit():
        name = form.name.data
        new_subject = Subject(name=name)
        db.session.add(new_subject)
        db.session.commit()
        flash(f'{name} added to the subjects', category='info')
    return render_template('content_management/add_subject.html', form=form)

@admin_bp.route('/ss_avail', methods=['GET'])
def ss_avail():
    '''
    ss_avail:
        this will get all available subjects
    '''
    cst = Subject.query.all()
    return render_template('admin/index.html', cst=cst)



