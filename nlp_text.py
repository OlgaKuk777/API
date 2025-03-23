import nltk
from nltk.corpus import stopwords
from pymorphy2 import MorphAnalyzer
from collections import Counter
#nltk.download('stopwords')
morph = MorphAnalyzer()

def process_text(text):
    stop_words = set(stopwords.words('russian'))
    addit_stop_words = ['это', 'весь', 'который', 'свой', 'мой', 'https']
    normalized_stop_words = set()

    for word in addit_stop_words:
        normalized_word = morph.parse(word)[0].normal_form
        normalized_stop_words.add(normalized_word)
        #print(f"Добавлено стоп-слово: {normalized_word}")

    stop_words.update(normalized_stop_words) # все сто-слова в одном месте

    words = nltk.word_tokenize(text.lower())
    #print(f"Токенизированные слова: {words}")

    filtered_words = [morph.parse(word)[0].normal_form for word in words
                      if word.isalpha() and morph.parse(word)[0].normal_form not in stop_words]

    #print(f"Слова после фильтрации: {filtered_words}")

    return Counter(filtered_words)
