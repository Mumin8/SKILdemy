import re
from gtts import gTTS
from googletrans import Translator

translator = Translator()

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
    return translator.translate(text=text, src='en', dest=lang).text


def process_for_arabic_vid(trans, matched, audio_path, lang):
    '''
        process the text to arabic  language
    '''
    
    ls = dict()
    text = reorganize(trans)
    start = 0
    for idx, word in enumerate(text):
        if word.lower() in matched:
            ls[f'{idx}{lang}'] = ' '.join(w for w in text[start:idx])
            ls[f'{idx}en'] = word.lower()
            start = idx+1
    ls[f'{idx}ar'] = ' '.join(w for w in text[start::])

    with open(audio_path, 'wb') as f:
        for k, v in ls.items():
            tts_ = gTTS(v, lang=k[-2::])
            tts_.write_to_fp(f)


def reorganize(trans):
    lines = trans.split('\n')
    organized = []
    for line in lines:
        organized.extend(reversed(line.split()))
    return organized


def process_for_other_lang_vid(trans, matched, audio_path, lang):
    ls = dict()
    lis = trans.split()
    
    start = 0
    for idx, word in enumerate(lis):
        if word.lower() in matched:
            ls[f'{idx}{lang}'] = ' '.join(w for w in lis[start:idx])
            ls[f'{idx}en'] = word.lower()
            start = idx+1
            lis[idx] = ''
    ls[f'{idx}{lang}'] = ' '.join(w for w in lis[start::])

    print(ls)
    with open(audio_path, 'wb') as f:
        for k, v in ls.items():
            print(f'the text : {v}')
            if v:
                tts_ = gTTS(v, lang=k[-2::])
                tts_.write_to_fp(f)
