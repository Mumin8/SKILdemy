import re
from gtts import gTTS
from googletrans import Translator

translator = Translator()



    

def find_matched_words(text1, text2):
    
    words_text1 = re.findall(r'\b\w+\b', text1.lower())
    
    words_text2 = re.findall(r'\b\w+\b', text2.lower())
    return set(words_text1) & set(words_text2)

def _translator(t):
    return translator.translate(text=t, src='en', dest='es').text



def from_eng_to_others():
    english_text = '''
    In python programming language, lists are very important. Functions are equally important too.
    to declare a function in python you start with the 
    keyword def followed by any name of your choice. To declare a list
    you have to type the name you want followed by = and then follow by the list keyword. There are some custom keywords in python
    such as the word lower, upper, capitalize and so on.
    '''
    trans = _translator(english_text)
    
    matched = find_matched_words(english_text, trans)

    ls = dict()
    lis = trans.split()
    start = 0
    for idx, word in enumerate(lis):
        if word.lower() in matched:
            ls[f'{idx}fr'] = ' '.join(w for w in lis[start:idx] )
            ls[f'{idx}en'] = word.lower()
            start = idx+1
   
    with open('some.mp3', 'wb') as f:
        for k, v in ls.items():
            tts_ = gTTS(v, lang=k[-2::])
            tts_.write_to_fp(f)
