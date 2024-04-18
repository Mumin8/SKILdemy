import os
import boto3
import secrets
from werkzeug.local import LocalProxy
from flask import g, session
from learning_platform import mongo


def get_db():
    db = getattr(g, "_database", None)

    if db is None:
        db = g._database = mongo.db
    return db


db = LocalProxy(get_db)


ALLOWED_EXTENSIONS = {'mp4'}


def acceptable(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def find_missing_vid(vid_list):
    set_values = {1, 2, 3, 4}
    print('did you get called')
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

    # clear_all_vids_list()
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
            "AWS_STORAGE_BUCKET_NAME"), "Key": video_name},
        ExpiresIn=3600)
    return url


def upload_s3vid(uploaded_file, filename):
    client = s3_client()
    client.upload_fileobj(uploaded_file, os.getenv(
        "AWS_STORAGE_BUCKET_NAME"), filename)


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
    c_dict[course.name] = [[t.name, course.id, t.id]
                           for topics in course.topics for t in topics.sub_topics]

    return c_dict


def read_content(course, topic):
    ''' 
    text_data:
        the approved videos will be handled by this
    '''

    content_ = db.text_display.find(
        {
            "$and": [
                {"course": course},
                {"topic": topic}
            ]
        }
    )

    return list(content_)[0]['desc']


def insert_text(code='f.PNG', desc=''):
    '''
    insert_text:
        this will insert text to a collection
    '''
    course = session.get('course')
    subject = session.get('subject')
    topic_name = session.get('subtopic')
    text_details = {
        "code": code, "desc": desc, "course": course,
        "subject": subject, "topic": topic_name
    }

    # collection name will change
    online_users = db.python_text_processing.insert_one(text_details)


def live_vid_content():
    all_videos = []
    col_content = db.student_shared_videos.find()
    all_videos.append(list(col_content))
    _list = _json(all_videos[0])
    return _list
