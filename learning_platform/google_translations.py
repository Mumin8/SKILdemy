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
        ['ar', 'bn', 'zh', 'en', 'es', 'fr', 'hi', 'id', 'pt', 'ru', 'tr', 'ur']
    )


def lang_detector(text):
    return translator.detect(text).lang


def find_matched_words(text):
    '''
    find the words that have not been translated
    '''
    pattern = r'\b[a-zA-Z]+\b'
    english_words = re.findall(pattern, text)
    print(english_words)
    return english_words


def text_translator(text, lang):
    '''
    translates the text to a language specified as lang
    '''
    text = translator.translate(text=text, src='en', dest=lang).text
    return text


def process_for_nonLatin(trans, matched, audio_path, lang):
    '''
    processes the text to another language
    '''

    ls = dict()
    lis = trans.split()
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
