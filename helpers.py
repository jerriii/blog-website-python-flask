import json


with open('config.json', 'r') as f:

    parameters = json.load(f)["parameters"]

UPLOAD_FOLDER = parameters['upload_location']


content_type_options = [
    {"value": "educational", "label": "Educational"},
    {"value": "entertainment", "label": "Entertainment"},
    {"value": "sports", "label": "Sports"},
]

profane_words = [
    "shit",
    "fuck",
    "bitch"
]
