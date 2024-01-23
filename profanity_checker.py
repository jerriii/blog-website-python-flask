import spacy
from profanity_filter import ProfanityFilter
from helpers import profane_words

nlp = spacy.load('en_core_web_sm')
pf = ProfanityFilter(nlps={'en': nlp})


def set_profane_extension(token):
    return token.text.lower() in profane_words
