
import secrets

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


