from bson import ObjectId
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    session,
    jsonify)
from flask_babel import gettext as _
from flask_login import login_required, current_user
from learning_platform import bcrypt, db
from learning_platform.forms.form import (
    Registration, CourseForm, TopicForm, SubTopicForm)
from learning_platform.models.models import (
    User, Course, SubTopic, Topic, TimeTask)
from functools import wraps
from learning_platform._helpers import (
    upload_s3vid_languages,
    live_vid_content,
    encryption,
    acceptable,
    insert_text,
    presigned_url,
    course_topic,
    c_and_topics,
    file_,
    delete_byID,
    exchange_rate,
    unlink_file,
    update_ai_text,
    update_by_id,
    update_trans_by_id,
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


def validate_subtopic_for_topic(topic_id, subtopic_id):
    '''
    validate_topic:
        this ensures there is no topic with the same name
    '''

    topics = Topic.query.get(topic_id)
    for t in topics.sub_topics:
        if t.id == subtopic_id:
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


def admin_required(f):
    @wraps(f)
    def dec_func(*args, **kwargs):
        if not current_user.is_authenticated or current_user.moderator != True:
            flash('Only admins allowed here', category='danger')
            return redirect(url_for('users.login'))
        return f(*args, **kwargs)
    return dec_func


@admin_bp.route('/reg_admin')
def reg_admin():
    username = 'Mumin8'
    fullname = 'Alhassan Mumin'
    email = 'alhassanmumin@gmail.com'
    admin_password = "my_pass_word"
    hashed = bcrypt.generate_password_hash(admin_password)
    moderator = True
    main_admin = User(fullname=fullname, username=username, email=email,
                      password=hashed, moderator=moderator)
    db.session.add(main_admin)
    db.session.commit()

    return "admin created successfully"


@admin_bp.route('/admin')
@admin_required
def admin():
    return render_template('admin/index.html')


@admin_bp.route('/create_user', methods=["GET"])
@login_required
@admin_required
def create_user():
    form = Registration(request.form)
    return render_template('user/register.html', form=form)


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


@admin_bp.route('/upload/<string:language>/<string:course_id>/<string:topic_id>',
                methods=['GET', 'POST'])
def upload(language, course_id, topic_id):
    validate_list()

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and acceptable(file.filename):
            course = Course.query.get(course_id)
            topic = SubTopic.query.get(topic_id)
            _name = f'{course.course_creator}{topic.topic_id}{topic.name}'

            name = encryption(_name) + '.mp4'

            upload_s3vid_languages(file, name, language)

            flash('successfully added the video', category='success')
        return redirect(url_for('admin.admin'))


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
        duration = form.duration.data
        creator = current_user.username
        rate = exchange_rate()
        new_course = Course(
            name=name,
            course_creator=creator,
            description=desc,
            price=price,
            duration=duration,
            rate=rate)
        timely = TimeTask(course=new_course)
        db.session.add(new_course)
        db.session.add(timely)
        db.session.commit()
        return jsonify({'message': 'Course created successfully'}), 201
    return render_template(
        'content_management/Register_course.html',
        form=form)


@admin_bp.route('/tim/')
@admin_bp.route('/tim/<string:c_id>')
def timely_topics(c_id):
    '''course to work with to be selected here
    '''
    if c_id != ' ':
        course = Course.query.get(c_id)
        c_and_t = c_and_topics(course)
        _, fv = next(iter(c_and_t.items()))
        return render_template('content_management/timely_asso.html', fv=fv)
    courses = Course.query.all()
    return render_template(
        'content_management/timely_course.html',
        courses=courses)


@admin_bp.route('/ctim/<string:stop_id>/<string:c_id>')
def course_timely_asso(stop_id, c_id):
    '''tasks will be added here
    '''
    course = Course.query.get(c_id)
    c_and_t = c_and_topics(course)
    _, fv = next(iter(c_and_t.items()))
    topic = SubTopic.query.get(stop_id)

    n = encryption(
        f'{course.course_creator}{topic.topic_id}{course.id}{topic.id}')

    for sub_topic in course.time_task.sub_topic:
        if sub_topic.name_a == n:
            flash('already associated', category='warning')
            break
    else:
        topic.update_name_a(n)
        course.time_task.sub_topic.append(topic)
        db.session.commit()
        flash('successfully added to delayed tasks', category='success')
    return render_template('content_management/timely_asso.html', fv=fv)


@admin_bp.route('/t/')
@admin_bp.route('/t/<string:c_id>')
def free_topics(c_id):
    if c_id != ' ':
        course = Course.query.get(c_id)
        c_and_t = c_and_topics(course)
        _, fv = next(iter(c_and_t.items()))
        return render_template(
            'content_management/course_free_topic.html', fv=fv)

    courses = Course.query.all()
    return render_template('content_management/courses.html', courses=courses)


@admin_bp.route('/cfass/<string:stop_id>/<string:c_id>')
def course_free_asso(stop_id, c_id):
    course = Course.query.get(c_id)
    trial = SubTopic.query.get(stop_id)

    c_and_t = c_and_topics(course)
    _, fv = next(iter(c_and_t.items()))

    if trial not in course.trial_topics:
        course.trial_topics.append(trial)
        flash('success', category='success')
        db.session.commit()
        return render_template(
            'content_management/course_free_topic.html', fv=fv)

    flash('already associated', category='warning')
    return render_template('content_management/course_free_topic.html', fv=fv)


@admin_bp.route('/cs_avail', methods=['GET', 'POST'])
def cs_avail():
    '''
    cs_avail:
        this will get all the available courses
    '''

    cst = Course.query.all()
    return render_template('content_management/delete_course.html', cst=cst)


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


@admin_bp.route('/c_s_st', methods=['GET', 'POST'])
def add_c_s_st():
    ''' this will add course, subject and sub topic to online ai content'''
    course = Course.query.all()
    subtopic = SubTopic.query.all()
    if request.method == "POST":
        session['course'] = request.form.get("course")
        session['subject'] = request.form.get("subject")
        session['subtopic'] = request.form.get("subtopic")
        insert_text()
        flash('successfully added content for ai video', category='success')
    return render_template(
        'content_management/course_subtopic.html',
        course=course,
        subtopic=subtopic)


@admin_bp.route('/reading_text', methods=['GET', 'POST'])
def add_reading_text():
    '''
    add_reading_text:
        this will add the skeleton of the reading text
    '''
    courses = Course.query.all()
    topics = SubTopic.query.all()

    if request.method == "POST":
        c_name = Course.query.get(request.form.get('course_id')).name
        t_name = SubTopic.query.get(request.form.get('topic_id')).name
        text_data(c_name, t_name)
        flash('added content ')
        return render_template(
            'content_management/reading_text.html',
            courses=courses,
            topics=topics)

    return render_template('content_management/reading_text.html',
                           courses=courses,
                           #  subjects=subjects,
                           topics=topics)


@admin_bp.route('/gpvid', methods=['GET'])
def get_published_Video():
    '''
    get_published_video:
        this will get all the published videos for visual display
    '''
    vid_content = live_vid_content()
    url = presigned_url('3957dc2fc92e347daa1d388e5b9b71eb.mp4')
    print(f'the url {vid_content}')
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

    session['course'] = Course.query.get(course_id).name
    session['topic'] = SubTopic.query.get(topic_id).name
    aud_vid(language)

    flash('video generated successfully', category='success')

    return render_template('admin/index.html')


@admin_bp.route('/admin_courses', methods=['GET', 'POST'])
def admin_all_course():
    language = request.form.get('language')
    session['lang'] = language
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
    lang = session.get('lang')
    contents = live_text_Display_AI_content()

    return render_template(
        'content_management/preview_ai_content.html',
        contents=contents,
        lang=lang)


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
            name = file_(request.files, 'UPLOAD_CODE_FOLDER')
            unlink_file(vid['code'], 'UPLOAD_CODE_FOLDER')
        update_by_id(ObjectId(_id), name, desc)
    return render_template(
        'content_management/update_ai_content.html',
        vid=vid)


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
        flash('text updated successfully', category='success')
        return redirect(url_for('admin.get_reading_text'))
    val = get_display_text_byID(ObjectId(_id))
    return render_template(
        'content_management/update_original.html',
        desc=val['desc'])


@admin_bp.route('/edit_trans/<string:_id>', methods=['GET', 'POST'])
def edit_translation(_id):
    '''It will update a particular field
    '''
    lang = session.get('lang')
    if request.method == 'POST':
        desc = request.form.get('desc')
        tream(ObjectId(_id), desc, lang)
        flash('text updated successfully', category='success')
        return redirect(url_for('admin.get_reading_text'))
    val = get_display_text_byID(ObjectId(_id))
    return render_template(
        'content_management/update_original.html',
        desc=val[lang])


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


@admin_bp.route('/t_ai_update/<string:_id>', methods=['GET', 'POST'])
def update_ai_translated_text(_id):
    '''
        It will update a particular field
    '''

    if request.method == 'POST':
        desc = request.form.get('desc')
        update_ai_text(ObjectId(_id), desc)
        flash('text updated successfully', category='success')
        return render_template('admin/index.html')

    vid = get_byID(ObjectId(_id))
    lang = session.get('lang')

    return render_template(
        'content_management/update_ai_transl.html',
        vid=vid,
        lang=lang)


@admin_bp.route('/ai_t_update/<string:_id>', methods=['GET', 'POST'])
def translate_ai_text(_id):
    '''
        It will update a particular field
    '''

    desc = get_byID(ObjectId(_id))
    update_trans_by_id(ObjectId(_id), desc['desc'])
    flash('text updated successfully', category='success')
    return render_template('admin/index.html')


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
    if request.method == "POST":
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            courses = user.enrolling
            return render_template(
                'content_management/user_courses.html',
                courses=courses,
                u_id=user.id)
        return render_template('content_management/user_courses.html')

    return render_template('content_management/user_email.html')


@admin_bp.route('/unenroll/<string:u_id>/<string:c_id>',
                methods=['GET', 'POST'])
def unenroll(c_id, u_id):
    '''
    user will be removed from here
    '''
    user = User.query.get(u_id)
    course = Course.query.get(c_id)

    user.enrolling.remove(course)
    db.session.commit()
    return redirect(url_for('admin.unenroll_user'))
