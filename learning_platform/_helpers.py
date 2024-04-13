
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
    set_values = {1,2,3,4}
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
    file_ext = '.' +  filename.rsplit('.', 1)[1].lower()
    random_name = secrets.token_hex(16)
    return f'{random_name}{file_ext}'


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
    video_ = db.python_videos.find(
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