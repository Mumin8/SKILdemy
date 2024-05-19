from bson import ObjectId
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_required, current_user, logout_user, login_user
from learning_platform import bcrypt, db
from werkzeug.utils import secure_filename
from learning_platform.forms.form import (
    Registration, LoginForm, CourseForm, TopicForm, SubjectForm, SubTopicForm)
from learning_platform.models.models import (
    User, Video, Course, SubTopic, Subject, YouTube, Topic, TimeTask)
from learning_platform._helpers import (
    hash_filename,
    live_vid_content,
    find_missing_vid,
    all_vids,
    acceptable,
    insertone,
    upload_s3vid,
    insert_text,
    presigned_url,
    course_topic,
    _file,
    delete_byID,
    unlink_file,
    update_by_id,
    live_text_Display_AI_content,
    user_courses,
    get_text_desc,
    recieve_displayed_text,
    get_byID,
    text_data,
    update_display_text,
    live_display_text_content,
    get_display_text_byID,
    delete_display_text_byID,
    tream)


admin_bp = Blueprint(
    'admin', __name__, static_folder='static', template_folder='templates')


v_id = []


def validate_topic_for_subject(subject_id, topic_id):
    subject = Subject.query.get(subject_id)
    for t in subject.topics:
        if t.id == topic_id:
            return False
    return True


def validate_subtopic_for_topic(course_id, topic_id):
    '''
    validate_topic:
        this ensures there is no topic with the same name
    '''

    topics = Topic.query.get(course_id)
    for t in topics.sub_topics:
        if t.id == topic_id:
            return False
    return True


def validate_topic_for_course(course_id, topic_id):
    '''
    validate_topic:
        this ensures there is no topic with the same name
    '''

    course = Course.query.get(course_id)
    for t in course.topics:
        print(f'{type(t.id)} and {type(topic_id)}')
        if t.id == topic_id:
            return False
    return True


def validate_subject(course_id, subject_id):
    '''
    validate_subject:
        this ensures there is no subject with the same name

    return
            True if no such subject exists and False otherwise
    '''
    course = Course.query.get(course_id)
    for s in course.subjects:
        if s.id == subject_id:
            return False
    return True


def validate_list():
    '''
    this will prepare the list for new  values
    '''
    if len(v_id) > 0:
        v_id.pop()


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
        if user and bcrypt.check_password_hash(
                user.password, form.password.data):
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
    return render_template(
        'admin/add_video.html',
        courses=courses,
        topics=topics)


@admin_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    validate_list()

    course = session.get('course')
    topic = session.get('topic')

    video_ = all_vids()
    v_id.append(video_)

    if len(v_id[0]) > 3:
        flash(
            'the number of videos is up to 4 alread, you will be notified if  a slop is available',
            category='success')
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
            if file and acceptable(file.filename):
                filename = secure_filename(file.filename)
                name = hash_filename(filename)
                _vid = find_missing_vid(v_id[0])
                file_details = {"video_id": str(
                    _vid), "name": name, "course": course, "topic": topic}
                upload_s3vid(file, name)
                # file.save(os.path.join(app.config['UPLOAD_FOLDER'], name))
                insertone(file_details)

                flash('successfully added the video', category='success')
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
    return render_template(
        'content_management/Register_course.html',
        form=form)


@admin_bp.route('/cs_avail', methods=['GET', 'POST'])
def cs_avail():
    '''
    cs_avail:
        this will get all the available courses
    '''

    cst = Course.query.all()
    return render_template('content_management/delete_course.html', cst=cst)


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
    return render_template('content_management/delete_language.html', cst=cst)


@admin_bp.route('/add_topic', methods=['GET', 'POST'])
def add_topic():
    '''
    add_topic:
        this will add a topic to the topic table
    '''
    form = TopicForm(request.form)
    if form.validate_on_submit():
        topic = form.name.data
        new_topic = Topic(name=topic)
        db.session.add(new_topic)
        db.session.commit()
        flash('added to the topics', category='info')
    return render_template('content_management/add_topic.html', form=form)


@admin_bp.route('/ts_avail', methods=['GET'])
def ts_avail():
    '''
    ts_avail:
        this will get all the available topics
    '''
    cst = Topic.query.all()
    return render_template('content_management/delete_topic.html', cst=cst)


@admin_bp.route('/add_subtopic', methods=['GET', 'POST'])
def add_sub_topic():
    '''
    add_sub_topic:
        this will add a topic to the topic table
    '''
    form = SubTopicForm(request.form)
    if form.validate_on_submit():
        subtopic = form.name.data
        new_subtopic = SubTopic(name=subtopic)
        db.session.add(new_subtopic)
        db.session.commit()
        flash(f'{subtopic} successfully added to the topics', category='info')
    return render_template('content_management/add_subtopic.html', form=form)


@admin_bp.route('/sts_avail', methods=['GET', 'POST'])
def sts_avail():
    '''
    ts_avail:
        this will get all the available sub topics
    '''
    cst = SubTopic.query.all()
    return render_template('content_management/delete_subtopic.html', cst=cst)


@admin_bp.route('/add_tc', methods=['GET', 'POST'])
def add_tc():
    '''
    add_tc:
        this will add a particular topic to a particular course
    '''
    courses = Course.query.all()
    topics = Topic.query.all()
    if request.method == "POST":
        course_id = request.form.get('course_id')
        topic_id = request.form.get('topic_id')
        topic = Topic.query.get(topic_id)
        status = validate_topic_for_course(course_id, topic_id)
        if status:
            course = Course.query.get(course_id)
            course.topics.append(topic)
            db.session.commit()
            flash(f'added {topic} to {course}', category='success')
            return render_template(
                'content_management/topic_to_course.html',
                courses=courses,
                topics=topics)
        else:
            flash('the topic is associated with this course', category='info')
            return render_template(
                'content_management/topic_to_course.html',
                courses=courses,
                topics=topics)

    return render_template(
        'content_management/topic_to_course.html',
        courses=courses,
        topics=topics)


@admin_bp.route('/add_sc', methods=['GET', 'POST'])
def add_sc():
    '''
    add_sc:
        this will add a particular subject to a particular course
    '''
    courses = Course.query.all()
    subjects = Subject.query.all()
    if request.method == "POST":
        course_id = request.form.get('course_id')
        subject_id = request.form.get('subject_id')
        subject = Subject.query.get(subject_id)
        course = Course.query.get(course_id)
        status = validate_subject(course_id, subject_id)
        if status:
            course = Course.query.get(course_id)
            course.subjects.append(subject)
            db.session.commit()
            flash(
                f'successfully added {subject} to {course}',
                category='success')
            return render_template(
                'content_management/subject_to_course.html',
                courses=courses,
                subjects=subjects)
        else:
            flash('this subject is associated with this course already',
                  category='info')
            return render_template(
                'content_management/subject_to_course.html',
                courses=courses,
                subjects=subjects)

    return render_template(
        'content_management/subject_to_course.html',
        courses=courses,
        subjects=subjects)


@admin_bp.route('/add_subtt', methods=['GET', 'POST'])
def add_subtt():
    '''
    add_tc:
        this will add a particular subtopic to a particular topic
    '''

    topics = Topic.query.all()
    subtopics = SubTopic.query.all()
    if request.method == "POST":
        topic_id = request.form.get('topic_id')
        subtopic_id = request.form.get('subtopic_id')
        subtopic = SubTopic.query.get(subtopic_id)
        status = validate_subtopic_for_topic(topic_id, subtopic_id)
        if status:
            topic = Topic.query.get(topic_id)
            topic.sub_topics.append(subtopic)
            db.session.commit()
            flash(f'successfully added {subtopic} to {topic}')
            return render_template(
                'content_management/subtopic_to_topic.html',
                subtopics=subtopics,
                topics=topics)
        else:
            flash(
                f'the topic is associated with this course',
                category='warning')
            return render_template(
                'content_management/subtopic_to_topic.html',
                subtopics=subtopics,
                topics=topics)

    return render_template(
        'content_management/subtopic_to_topic.html',
        subtopics=subtopics,
        topics=topics)


@admin_bp.route('/add_ts', methods=['GET', 'POST'])
def add_topic_to_subject():
    '''
    add_tc:
        this will add a particular topic to a particular subject
    '''
    subjects = Subject.query.all()
    topics = Topic.query.all()
    if request.method == "POST":
        subject_id = request.form.get('subject_id')
        topic_id = request.form.get('topic_id')

        topic = Topic.query.get(topic_id)

        status = validate_topic_for_subject(subject_id, topic_id)
        if status:
            subject = Subject.query.get(subject_id)
            subject.topics.append(topic)
            db.session.commit()
            flash(
                f'successfully added {topic} to {subject}', category='success')
            return render_template(
                'content_management/topic_to_subject.html',
                subjects=subjects,
                topics=topics)
        else:
            flash('the topic is associated with this course', category='info')
            return render_template(
                'content_management/topic_to_subject.html',
                subjects=subjects,
                topics=topics)

    return render_template(
        'content_management/topic_to_subject.html',
        subjects=subjects,
        topics=topics)


@admin_bp.route('/c_s_st', methods=['GET', 'POST'])
def add_c_s_st():
    ''' this will add course, subject and sub topic to online ai content'''
    course = Course.query.all()
    subject = Subject.query.all()
    subtopic = SubTopic.query.all()
    if request.method == "POST":
        session['course'] = request.form.get("course")
        session['subject'] = request.form.get("subject")
        session['subtopic'] = request.form.get("subtopic")
        insert_text()
        flash('successfully added content for ai video')
    return render_template(
        'content_management/course_subject_subtopic.html',
        course=course,
        subject=subject,
        subtopic=subtopic)


@admin_bp.route('/reading_text', methods=['GET', 'POST'])
def add_reading_text():
    '''
    add_reading_text:
        this will add the skeleton of the reading text
    '''
    courses = Course.query.all()
    subjects = Subject.query.all()
    topics = SubTopic.query.all()

    if request.method == "POST":
        c_name = Course.query.get(request.form.get('course_id')).name
        s_name = Subject.query.get(request.form.get('subject_id')).name
        t_name = SubTopic.query.get(request.form.get('topic_id')).name
        text_data(c_name, s_name, t_name)
        flash('added content ')
        return render_template(
            'content_management/reading_text.html',
            courses=courses,
            subjects=subjects,
            topics=topics)

    return render_template('content_management/reading_text.html',
                           courses=courses, subjects=subjects, topics=topics)


@admin_bp.route('/gpvid', methods=['GET'])
def get_published_Video():
    '''
    get_published_video:
        this will get all the published videos for visual display
    '''
    vid_content = live_vid_content()
    url = presigned_url('3957dc2fc92e347daa1d388e5b9b71eb.mp4')
    # print(f'the url {vid_content}')
    return render_template(
        'content_management/preview_shared_videos.html',
        url=url)


@admin_bp.route('/gtv', methods=['GET', 'POST'])
@login_required
def aud_vid(lang):
    '''
    aud_vid:
        this is where the audio video clip thing starts
    '''

    v = get_text_desc()
    acc_v = recieve_displayed_text(v, lang)

    # else:
    #     acc_v = recieve_displayed_text_others(str(current_user.id), v, lang)

    return acc_v


@admin_bp.route('/gptplus/<string:language>/<string:course_id>/<string:topic_id>',
                methods=['GET', 'POST'])
@login_required
def gptplus(language, course_id, topic_id):
    '''
    gptplus:
        this is where the ai video is processed
    '''
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))

    user_c = sorted(user_courses(current_user.id))
    c_and_t = course_topic(user_c)
    session['course'] = Course.query.get(course_id).name
    session['topic'] = SubTopic.query.get(topic_id).name
    path = aud_vid(language)
    paths = path.split('myvideo')
    flash('video generated successfully', category='success')

    return render_template('admin/index.html')


@admin_bp.route('/admin_courses', methods=['GET', 'POST'])
def admin_all_course():
    language = request.form.get('language')
    user_c = user_courses()
    c_and_t = course_topic(user_c)
    return render_template(
        'content_management/generate_ai_video.html',
        dict_v=c_and_t,
        language=language)


@admin_bp.route('/gpai', methods=['GET'])
def get_published_AI():
    '''
    get_published_AI:
        this will get the AI content for analysis
    '''
    contents = live_text_Display_AI_content()

    return render_template(
        'content_management/preview_ai_content.html',
        contents=contents)


@admin_bp.route('/updatePAI/<string:_id>', methods=['GET', 'POST'])
def update_published_AI(_id):
    '''
    update_published_AI:
        the text and code snippet will be updated here
    '''
    vid = get_byID(ObjectId(_id))
    if request.method == 'POST':
        desc = request.form.get('desc')
        name = None
        if request.files['file']:
            name = _file(request.files, 'UPLOAD_CODE_FOLDER')
            unlink_file(vid['code'], 'UPLOAD_CODE_FOLDER')
        update_by_id(ObjectId(_id), name, desc)
    return render_template(
        'content_management/update_ai_content.html',
        vid=vid)


@admin_bp.route('/add_tt', methods=['GET', 'POST'])
def add_tt():
    '''
    add_tt:
        this will add tasks that will be delayed to the database
    '''

    if request.method == "POST":
        task_id = request.form.get('topic_id')
        usertask = SubTopic.query.get(task_id).name
        if usertask:
            new_task = TimeTask(usertask=usertask, id=task_id)
            db.session.add(new_task)
            db.session.commit()
            flash('added to delayed tasks', category='success')
            return redirect(url_for('admin.add_tt'))

    avail_tasks = SubTopic.query.all()
    return render_template(
        'content_management/timely_task.html',
        avail_tasks=avail_tasks)


@admin_bp.route('/you-tube', methods=['GET', 'POST'])
def add_youtube_vid():
    subtopic = SubTopic.query.all()
    if request.method == 'POST':
        subtopic_id = request.form.get('subtopic_id')
        if not subtopic_id:
            flash('select the topic', category='warning')
            return redirect(url_for('admin.add_youtube_vid'))

        content = request.form.get('iframe_content')
        if not content:
            flash('you did not include the content', category='warning')

        youtube = YouTube()
        youtube.subtopic_id = subtopic_id

        f, s = content.split("src=")
        youtube_link, trash = s.split('title')
        youtube.link = youtube_link
        db.session.add(youtube)
        db.session.commit()
        flash('you have added a link to a youtube video', category='success')
    return render_template(
        'content_management/add_youtube_video.html',
        subtopic=subtopic)


@admin_bp.route('/del_course/<string:c_id>', methods=['GET'])
def del_course(c_id):
    '''
    del_course:
        this will delete the course with id = s_id from the database
    '''
    try:
        course = Course.query.filter_by(id=c_id).first()
        db.session.delete(course)
        db.session.commit()
        return render_template('admin/index.html')
    except BaseException:
        return "something went wrong"


@admin_bp.route('/del_lang/<string:s_id>', methods=['GET'])
def del_lang(s_id):
    '''
    del_lang:
        this will delete the language or subject with id = s_id from the database
    '''
    try:
        language = Subject.query.filter_by(id=s_id).first()
        db.session.delete(language)
        db.session.commit()
        return render_template('admin/index.html')
    except BaseException:
        return 'something went wrong'


@admin_bp.route('/del_topic/<string:t_id>', methods=['GET'])
def del_topic(t_id):
    '''
    del_topic:
        this will delete the topic with id = t_id from the database
    '''
    try:
        topic = Topic.query.filter_by(id=t_id).first()
        db.session.delete(topic)
        db.session.commit()
        return render_template('admin/index.html')
    except BaseException:
        return "something went wrong"


@admin_bp.route('/del_subtopic/<string:st_id>', methods=['GET'])
def del_subtopic(st_id):
    '''
    del_subtopic:
        this will delete the subtopic with id = st_id from the database
    '''
    try:
        subtopic = SubTopic.query.filter_by(id=st_id).first()
        db.session.delete(subtopic)
        db.session.commit()
        flash(f'{subtopic.name} deleted successfully', category='info')
        return render_template('admin/index.html')
    except BaseException:
        return "something went wrong"


@admin_bp.route('/del_image/<string:_id>', methods=['GET'])
def delete_ai_image(_id):
    try:
        vid = get_byID(ObjectId(_id))
        unlink_file(vid['code'], 'UPLOAD_CODE_FOLDER')
        delete_byID(_id)
    except ValueError as e:
        try:
            delete_byID(_id)
            return f'(No image itself {e})'
        except BaseException:
            return 'failure'
    return 'success'


@admin_bp.route('/gptd', methods=['GET', 'POST'])
def get_reading_text():
    '''
    get_published_AI:
        this will get the AI content for analysis
    '''
    lang = request.form.get('language')

    session['lang'] = lang
    contents = live_display_text_content()

    return render_template(
        'content_management/preview_text_to_translate.html',
        contents=contents,
        lang=lang)


@admin_bp.route('/tream/<string:_id>', methods=['GET', 'POST'])
def tream_original(_id):
    '''It will update a particular field
    '''
    if request.method == 'POST':
        desc = request.form.get('desc')
        tream(ObjectId(_id), desc)
        flash('text updated successfully')
        return redirect(url_for('admin.get_reading_text'))
    val = get_display_text_byID(ObjectId(_id))
    return render_template(
        'content_management/update_original.html',
        desc=val['desc'])


@admin_bp.route('/t_update/<string:_id>', methods=['GET', 'POST'])
def update_text(_id):
    '''
        It will update a particular field
    '''

    if request.method == 'POST':
        desc = request.form.get('desc')
        update_display_text(ObjectId(_id), desc)
        flash('text updated successfully', category='success')
        return render_template('admin/index.html')
    vid = get_display_text_byID(ObjectId(_id))
    return render_template(
        'content_management/update_display_text.html',
        vid=vid)


@admin_bp.route('/del_txt_d/<string:_id>', methods=['GET'])
def delete_display_text(_id):
    '''
        It will delete the record for the reading
    '''
    delete_display_text_byID(ObjectId(_id))
    flash('successfully deleted the record', category='info')
    return redirect(url_for('admin.get_reading_text'))



@admin_bp.route('/unenroll_user', methods=['GET', 'POST'])
def unenroll_user():
    '''
    Get user based on email
    '''
    if request.method=="POST":
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            courses = user.enrolling
            return render_template('content_management/user_courses.html', courses=courses, u_id=user.id)
        return render_template('content_management/user_courses.html')
        
    return render_template('content_management/user_email.html')


@admin_bp.route('/unenroll/<string:u_id>/<string:c_id>', methods=['GET', 'POST'])
def unenroll(c_id, u_id):
    '''
    user will be removed from here
    '''
    user = User.query.get(u_id)
    course = Course.query.get(c_id)
    
    user.enrolling.remove(course)
    db.session.commit()
    return redirect(url_for('admin.unenroll_user'))
    