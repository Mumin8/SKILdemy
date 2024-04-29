import googletrans
from googletrans import Translator

translator = Translator()


def _detected_language(text):
    return translator.detect(text).lang 

def _translator(t):
    
    return translator.translate(text=t, src=_detected_language(t), dest='ar').text
    


