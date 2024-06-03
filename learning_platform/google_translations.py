import re
from flask import g, request, session
from gtts import gTTS
from googletrans import Translator


translator = Translator()


def get_locale():
    '''
    get the user locale
    '''
    lang = session.get('lang')
    if lang:
        return lang
    
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale

    return request.accept_languages.best_match(
        ['ar', 'bn', 'zh-CN', 'en', 'es', 'fr', 'hi', 'id', 'pt', 'ru', 'tr', 'ur']
    )


# def get_timezone():
#     user = getattr(g, 'user', None)
#     if user is not None:
#         return user.timezone

def lang_detector(text):
    return translator.detect(text).lang


def find_matched_words(text1, text2):
    '''
    find the words that have not been translated
    '''
    words_text1 = re.findall(r'\b\w+\b', text1.lower())
    words_text2 = re.findall(r'\b\w+\b', text2.lower())
    return set(words_text1) & set(words_text2)


def text_translator(text, lang):
    '''
    translates the text to a language specified as lang
    '''
    text = translator.translate(text=text, src='en', dest=lang).text
    return text


def reorganize(trans):
    '''
    reorganize the arabic to read like the rest of the languages
    '''
    lines = trans.split('\n')
    organized = []
    for line in lines:
        organized.extend(reversed(line.split()))
    return organized


def process_for_arabic_vid(trans, matched, audio_path, lang):
    '''
        process the text to arabic  language
    '''
    _trans = reorganize(trans)
    process_for_nonArabic(trans, matched, audio_path, lang)


def process_for_nonArabic(trans, matched, audio_path, lang):
    '''
    processes the text to aanother language
    '''
    latin_alphabet = {'pt', 'fr', 'es', 'id', 'tr', 'en'}
    ls = dict()

    if isinstance(trans, list):
        lis = trans
    elif lang not in latin_alphabet:
        lis = trans.split()

    if lang in latin_alphabet:
        tts_ = gTTS(trans, lang=lang)
        tts_.save(audio_path)
    else:
        start = 0
        for idx, word in enumerate(lis):
            if word.lower() in matched:
                ls[f'{idx}{lang}'] = ' '.join(
                    w for w in lis[start:idx]).strip()
                ls[f'{idx}en'] = word.lower()
                start = idx + 1
                lis[idx] = ''
        if lis[start::]:
            ls[f'{idx}{lang}'] = ' '.join(w for w in lis[start::]).strip()

        with open(audio_path, 'wb') as f:
            for k, v in ls.items():
                if v:
                    tts_ = gTTS(v, lang=k[-2::])
                    tts_.write_to_fp(f)
