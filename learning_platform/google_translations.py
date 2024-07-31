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
    print('nothing here is added')
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

def get_duration(audio_path, text, lang):
    with open(audio_path, 'wb') as f:
        speech = gTTS(text, lang=lang)
        speech.write_to_fp(f)
    
       

def process_for_nonLatin(text, audio_path, lang):
    '''
    processes the text to another language
    '''
    with open(audio_path, 'wb') as f:
        tts_ = gTTS(text, lang=lang)
        tts_.write_to_fp(f)
