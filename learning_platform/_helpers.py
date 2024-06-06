import os, re
import boto3
import secrets
import shutil
import requests
import pyttsx3
from bson.objectid import ObjectId
from werkzeug.local import LocalProxy
from flask import g, session, flash, redirect, url_for, request
from flask_login import current_user
from learning_platform import mongo, app
from datetime import datetime, timedelta
from moviepy.editor import (AudioFileClip, concatenate_videoclips,
                            VideoFileClip, ImageClip)
from werkzeug.utils import secure_filename
from learning_platform.google_translations import (
    text_translator, find_matched_words, process_for_nonArabic,
    process_for_arabic_vid, get_locale)
from learning_platform.models.models import Course, TimeTask, User

my_audio_video = 'output_folder/'

cache = {}


# def update_dict(_cache):
#     cache = _cache
    


def get_dict():
    return cache


def get_ref():
    return secrets.token_urlsafe(50)


def get_db():
    db = getattr(g, "_database", None)

    if db is None:
        db = g._database = mongo.db
    return db


db = LocalProxy(get_db)


def acceptable(filename):
    ALLOWED_EXT = {'mp4'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def allowed_file(filename):
    '''
    allowed_file:
        this will validate the allowed files
    '''
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _file(files, _dir):
    '''
    _file:
        this will save file
    '''
    if 'file' not in files:
        flash('No file part')
        return redirect(request.url)
    file = files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        name = hash_filename(filename)
        file.save(os.path.join(app.config[_dir], name))

    return name


def unlink_file(name, _dir):
    '''
    unlink_file:
        this will delete the unneeded files from the directory
    args:
        name: this is the name of the file
        _dir: this is the directory in which the file is
    '''
    try:
        os.unlink(os.path.join(app.config[_dir], name))
    except FileNotFoundError:
        return 'no file found'


def find_missing_vid(vid_list):
    set_values = {1, 2, 3, 4}
    my_list = []
    for v_item in vid_list:
        # print(v_item)
        my_list.append(v_item)
        my_list.append(int(v_item['video_id']))
    for s_v in set_values:
        if s_v not in my_list:
            return s_v


def hash_filename(filename):
    file_ext = '.' + filename.rsplit('.', 1)[1].lower()
    random_name = secrets.token_hex(16)
    return f'{random_name}{file_ext}'


def _json(l):
    for i, o in enumerate(l):
        print(f"the description {o}")
        l[i]['_id'] = str(o['_id'])
    return l


def all_vids():
    '''
    This will get all videos from mongodb
    Return:
            the vidoes object in a list
    '''
    course = session.get('course')
    topic = session.get('topic')
    print(f'lan {course} and top {topic}')

    video_ = db.student_shared_videos.find(
        {
            "$and": [
                {"course": course},
                {"topic": topic}
            ]
        }
    )
    return list(video_)


def insertone(_dict):
    db.student_shared_videos.insert_one(_dict)


def s3_client():
    s3_client = boto3.client("s3",
                             aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                             aws_secret_access_key=os.getenv(
                                 "AWS_SECRET_ACCESS_KEY"),
                             region_name='us-east-1')

    return s3_client


def presigned_url(video_name):
    client = s3_client()
    url = client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": os.getenv(
            f"AWS_STORAGE_BUCKET_NAME{get_lang()}"), "Key": video_name},
        ExpiresIn=3600)
    return url


def upload_s3vid(uploaded_file, filename):
    client = s3_client()
    client.upload_fileobj(uploaded_file, os.getenv(
        "AWS_STORAGE_BUCKET_NAME"), filename)


def upload_s3vid_languages(uploaded_file, filename, lang):
    client = s3_client()
    with open(uploaded_file, 'rb') as file_obj:
        client.upload_fileobj(file_obj, os.getenv(
            f"AWS_STORAGE_BUCKET_NAME{lang}"), filename)


def get_byID(_id):

    video_ = db.ai_video_text.find_one({'_id': _id})
    return video_


def update_by_id(_id, code, desc):
    update_fields = {}

    if desc is not None:
        update_fields['desc'] = desc
    if code != '' and code is not None:
        update_fields['code'] = code

    result = db.ai_video_text.update_one(
        {'_id': _id},
        {'$set': update_fields}
    )

    return result


def update_trans_by_id(_id, desc):
    update_fields = {}
    lang = session.get('lang')

    if desc is not None:
        update_fields[lang] = text_translator(desc, lang)
    print(update_fields)

    result = db.ai_video_text.update_one(
        {'_id': _id},
        {'$set': update_fields}
    )

    return result


def course_topic(course):
    """
    validate_topic:
        this ensures there is no topic with the same name
    arg:
        course_list: the list of all the courses
    return:
        True if no such topic exists and False otherwise
    """

    c_dict = {}

    for idx, cl in enumerate(course):
        course = Course.query.get(cl[-1])
        c_dict[course.name] = [[t.name, course.id, t.id]
                               for topics in course.topics for t in topics.sub_topics]

    return c_dict


def c_and_topics(course):
    c_dict = {}
    c_dict[course.name] = [[t.name, course.id, t.id]
                           for topics in course.topics for t in topics.sub_topics]

    return c_dict


def deque_dict(orig_dic, first):
    mod_dic = {}
    mod_dic[first] = orig_dic[first]
    l = list(orig_dic)

    for i in l:
        mod_dic[i] = orig_dic[i]

    return mod_dic



def vid_iframes(text):
    iframe = []
    pattern = r'(<iframe\s+[^>]*src=["\']https?://(?:www\.)?youtube\.com/embed/[^"\']+["\'][^>]*></iframe>)'
    frames_l = re.findall(pattern, text)
    modified_text = re.sub(pattern, '', text)

    for l in frames_l:
        f, s = l.split("src=")
        _link, trash = s.split('title')
        _, l = _link.split('embed/')
        iframe.append(l)
    
    return modified_text, iframe

def cached(course, topic):
    
    global cache

    if course not in cache.keys():
        cache[course] = {}
        cache[course][get_lang()] = {}
        cache[course][get_lang()][topic] = {}
        cache[course][get_lang()][topic]['desc'] = read_content(course, topic)

        if len(cache) > 10:
            idx = list(cache)[-1]
            cache.pop(idx)
    else:
        cache = deque_dict(cache, course)
        if get_lang() not in cache[course].keys():
            cache[course][get_lang()] = {}
            cache[course][get_lang()][topic] = {}
            cache[course][get_lang()][topic]['desc'] = read_content(course, topic)

            if len(cache[course]) > 10:
                idx = list(cache[course])[-1]
                cache[course].pop(idx)
        else:
            cache[course] = deque_dict(cache[course], get_lang())
            if topic not in cache[course][get_lang()].keys():
                cache[course][get_lang()][topic] = {}
                cache[course][get_lang()][topic]['desc'] = read_content(
                    course, topic)

                if len(cache[course][get_lang()]) > 10:
                    idx = list(cache[course][get_lang()])[-1]
                    cache[course][get_lang()].pop(idx)

            else:
                cache[course][get_lang()] = deque_dict(
                    cache[course][get_lang()], topic)

    # update_dict(cache)
    text = cache[course][get_lang()][topic]['desc']
    _text, iframes = vid_iframes(text)
    print(f'the text {_text} and the list {iframes}')
  
    return _text, iframes


def read_content(course, topic):
    '''
    text_data:
        the approved videos will be handled by this
    '''

    my_list = []
    content_ = db.text_display.find(
        {
            "$and": [
                {"course": course},
                {"topic": topic}
            ]
        }
    )
    my_list.append(list(content_))

    if my_list[0]:
        return my_list[0][0][get_lang()]
    return 'Nothing published. stay tuned'


def get_lang():
    user_locale = get_locale()
    lang = session.get('lang')
    if lang is None:
        lang = user_locale
    return lang


def _auth():
    auth = False
    if current_user.is_authenticated:
        auth = True
    return auth


def insert_text(code='f.PNG', desc=None, en=None,
                ru=None, es=None, hi=None, ar=None, fr=None,
                ur=None, bn=None, pt=None, zh=None, tr=None,
                id=None):
    '''
    insert_text:
        this will insert text to a collection
    '''
    course = session.get('course')
    subject = session.get('subject')
    topic = session.get('subtopic')
    text_details = {
        "code": code,
        "desc": desc,
        "course": course,
        "language": subject,
        "topic": topic,
        "en": en,
        "ar": ar,
        "bn": bn,
        'fr': fr,
        "tr": tr,
        "es": es,
        "pt": pt,
        "ur": ur,
        "ru": ru,
        "hi": hi,
        "zh": zh,
        "id": id
    }

    db.ai_video_text.insert_one(text_details)


def get_text_desc():
    '''
    get_text_desc:
        this will query the mongodb collection for a match
    '''
    _course = session.get('course')
    _topic = session.get('topic')
    print(f'the course name {_course} and the topic name {_topic}')

    video_ = db.ai_video_text.find(
        {
            "$and": [
                {"course": _course},
                {"topic": _topic}
            ]

        }
    )
    return list(video_)


def live_vid_content():
    all_videos = []
    col_content = db.student_shared_videos.find()
    all_videos.append(list(col_content))
    _list = _json(all_videos[0])
    return _list


def create_audio_clip(text, output_path):
    '''
    create_audio_clip:
        this will read the text
    args:
        text:   the string of text to read
        output_path: the path to the synthesized audio
    '''
    tts(text, output_path)


def create_video_clip(text, output_path, duration, folder):
    '''
    create_video_clip:
        this will create the video clip
    '''
    if not current_user.is_authenticated:
        return redirect(url_for('users.admin_login'))

    # video_duration = duration
    audio_clip_path = str(current_user.id) + "_"'temp_audio.mp3'

    path_aud = os.path.join(folder, audio_clip_path)

    create_audio_clip(text, path_aud)

    video_clip = ImageClip(text, duration=duration)

    video_clip = video_clip.set_audio(AudioFileClip(path_aud))

    # Write the final video clip to the specified output path
    video_clip.write_videofile(
        output_path, codec='libx264', audio_codec='aac', fps=24)

    os.remove(path_aud)


def join_clips(res_clips, lang):
    '''
    join_clips:
        this will join all the clips together
    return:
        the final output path
    '''
    root_path = app.root_path
    comp_file = f'{session.get("course")}_{session.get("topic")}.mp4'
    output_p = os.path.join(root_path, 'static', 'myvideo', comp_file)

    clips_list = []

    for _clip in res_clips:
        clips_list.append(VideoFileClip(_clip))

    final_c = concatenate_videoclips(clips_list, method="compose")

    final_c.write_videofile(output_p)

    upload_s3vid_languages(output_p, comp_file, lang)

    return output_p


def tts(text, output_path):
    '''
    tts:
        this will instance text to speech and set the properties
    '''
    lang = session.get('lang')

    print(f'the language: {session.get("lang")}')
    if lang == "en":
        v = 'Microsoft David Desktop - English (United States)'
    elif lang == 'es':
        v = "Microsoft Helena Desktop - Spanish (Spain)"
    elif lang == 'pt':
        v = "Microsoft Helia - Portuguese (Portugal)"
    elif lang == 'id':
        v = "Microsoft Andika - Indonesian (Indonesia)"
    elif lang == 'tr':
        v = "Microsoft Tolga - Turkish (Turkey)"
    elif lang == 'fr':
        v = "Microsoft Hortense Desktop - French"
    
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')  
    for voice in voices:
        if voice.name == v:
            engine.setProperty(voice, voice.id)
            break
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 0.9)
    engine.setProperty('pitch', 50)
    engine = pyttsx3.init()
    engine.save_to_file(text, output_path)
    engine.runAndWait()


def recieve_displayed_text(vid_list, lang):
    '''
    recieve_displayed_text:
        It will read the text from Mongodb
    arg:
        vid_list: the list of videos
    '''

    res_clips = []
    root_path = app.root_path

    for i, _d in enumerate(vid_list):
        audio_file = f'temp_slide_audio_{i}.mp3'
        video_file = f'temp_slide_video_{i}.mp4'

        audio_path = os.path.join(my_audio_video, audio_file)
        video_path = os.path.join(my_audio_video, video_file)

        # arabic_alphabet = {'ar', 'urdu'}
        latin_alphabet = {'ru', 'hi', 'bn', 'zh'}
        sp_lat_alphabet = {'pt', 'fr', 'es', 'id', 'tr', 'en'}
        matched = find_matched_words(_d["desc"], _d[lang])
        if lang in latin_alphabet:
            process_for_nonArabic(_d[lang], matched, audio_path, lang)
            
        elif lang in sp_lat_alphabet:
            create_audio_clip(_d[lang], audio_path)
        else:
            process_for_arabic_vid(_d[lang], matched, audio_path, lang)

        slide_audio_clip = AudioFileClip(audio_path)

        final_clip_duration = slide_audio_clip.duration
        create_video_clip(
            f'{root_path}/static/default/code/{vid_list[i]["code"]}',
            video_path, final_clip_duration, my_audio_video
        )
        slide_video_clip = VideoFileClip(video_path)

        slide_audio_clip = slide_audio_clip.set_duration(final_clip_duration)

        slide_video_clip = slide_video_clip.set_duration(final_clip_duration)
        cl = slide_video_clip.set_audio(slide_audio_clip)

        output_p = os.path.join(root_path, 'static', 'video_lists', video_file)
        res_clips.append(output_p)
        cl.write_videofile(output_p)

    final_output_path = join_clips(res_clips, lang)

    return final_output_path


def matched_dic(matched, text_list):
    match_dict = dict()
    for v in matched:
        _n = text_list.count(v)
        match_dict[v] = _n
    return match_dict


def live_text_Display_AI_content():
    all_videos = []
    col_content = db.ai_video_text.find()
    all_videos.append(list(col_content))

    _list = _json(all_videos[0])
    return _list


def user_courses(id=None):
    course_list = []
    if id:
        courses = current_user.enrolling
    else:
        courses = Course.query.all()
    try:
        for c in courses:
            course_list.append([])
            course_list[-1].append(c.name)
            course_list[-1].append(c.id)

        return course_list
    except AttributeError:
        flash('Please login to access this page', category='success')
        return redirect(url_for('users.admin_login'))


def copy_ai_video(vid_path, dest_path):
    if not current_user.is_authenticated:
        return redirect(url_for('users.login'))
    name = f'{current_user.id}_video_file.mp4'
    shutil.copyfile(vid_path, os.path.join(dest_path, name))
    return name


def validate_time_task(user_id, task_id, task_name):
    timely_task = TimeTask.query.filter_by(usertask=task_name).first()

    if timely_task is None:
        return True, "Not timely"
    else:
        task = TimeTask.query.filter_by(user_id=user_id, id=task_id).first()

        if task:
            status, _task = task_pending(user_id)
            if status:
                return status, "Not timely"
            else:
                # the time for the solution is not yet up so solution will not
                # be ready
                elapsed_time = datetime.now() - task.updated_at
                hours, minutes, seconds = f'{timedelta(days=1) - elapsed_time}'.split(
                    ':')
                flash(
                    f'''{_task} is already pending
                        solution will be available in {hours} hr, {minutes} MIN
                        But you can decline the previous pending task if you want this rather
                        ''', category='info')
                return status, "pending"
        else:
            flash('please request for the solution')
            return False, "request"


def vid_ids(rel_vid):
    ids_list = []
    for v in rel_vid:
        _, path = v.link.split("embed/")
        ids_list.append(path)
    return ids_list


def task_pending(user_id):
    user = User.query.get(user_id)
    print('never called')
    for tt in user.time_task:
        elapsed_time = datetime.now() - tt.updated_at
        waiting_period = timedelta(days=1)
        if elapsed_time <= waiting_period:
            print(f'pending {tt} and {tt.usertask}')
            return False, tt.usertask

    return True, None


def verify_payment(ref):
    '''
    verify_payment:
            this is where the payment is verified
    '''
    PAYSTACK_SK = os.getenv("PAYSTACK_SECRET_KEY")
    base_url = "https://api.paystack.co/"
    path = f'transaction/verify/{ref}'
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SK}",
        "Content-Type": "application/json",
    }

    url = base_url + path
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        return True, response_data['data']

    response_data = response.json()
    return False, response_data['message']


def delete_byID(_id):
    '''
        Delete the field with the _id
    '''
    db.ai_video_text.delete_one({'_id': ObjectId(_id)})


def text_data(course, topic, desc=None, en=None,
              ru=None, es=None, hi=None, ar=None, fr=None,
              ur=None, bn=None, pt=None, zh=None, tr=None,
              id=None):
    '''
    text_data:
        structure of the reading text
    '''
    file_details = {
        "course": course,
        "topic": topic,
        "desc": desc,
        "en": en,
        "ar": ar,
        "bn": bn,
        'fr': fr,
        "tr": tr,
        "es": es,
        "pt": pt,
        "ur": ur,
        "ru": ru,
        "hi": hi,
        "zh": zh,
        "id": id}
    db.text_display.insert_one(file_details)


def live_display_text_content():
    '''
        Processes the text that will be displayed
    '''
    all_videos = []
    col_content = db.text_display.find()
    all_videos.append(list(col_content))

    _list = _json(all_videos[0])
    return _list


def get_display_text_byID(_id):
    '''
        Retrieve the text in the field with _id
    '''
    video_ = db.text_display.find_one({'_id': _id})
    return video_


def tream(_id, text, lang=None):
    '''
        Edit the original text in the field
    '''
    update_fields = {}
    if lang is None:
        update_fields['desc'] = text
    else:
        update_fields[lang] = text

    result = db.text_display.update_one(
        {'_id': _id},
        {'$set': update_fields}
    )

    return result


def update_display_text(_id, desc):
    '''
        populate other fields with the described text
    '''
    lang = session.get('lang')
    update_fields = {}
    update_fields[lang] = text_translator(desc, lang)

    result = db.text_display.update_one(
        {'_id': _id},
        {'$set': update_fields}
    )

    return result


def update_ai_text(_id, desc):
    '''
        populate other fields with the described text
    '''
    lang = session.get('lang')
    update_fields = {}
    update_fields[lang] = desc

    result = db.ai_video_text.update_one(
        {'_id': _id},
        {'$set': update_fields}
    )

    return result


def delete_display_text_byID(_id):
    '''
        Delete the record with the _id
    '''
    db.text_display.delete_one({'_id': _id})


def exchange_rate():
    '''
    gets the exchange rate for the course
    '''
    url = "https://openexchangerates.org/api/latest.json?app_id=72d8b9a87a934d46afb186e51fd18a8e&base=USD&symbols=GHS"

    response = requests.get(url)
    data = response.json()
    return data["rates"]["GHS"]


def time_():
    '''
    checks if the time is up to update the rate
    '''
    courses = Course.query.all()

    course = next(iter(courses))

    elapsed_time = datetime.now() - course.get_updated()
    if elapsed_time >= timedelta(hours=1):
        return True, datetime.now()
    return False, datetime.now()


def completed_course(course):
    '''
    check if the user is ready to retrieve certificate
    '''
    elapsed_time = datetime.now() - course.enrolled_at
    if elapsed_time >= timedelta(days=90):
        return True
    return False
