import json


def filter_poem_data():

    poem_data = json.load(open("poems.json", "r", encoding="utf-8"))

    full_poem_author_data = json.load(open("poems_list_data.json", "r", encoding="utf-8"))

    poem_full_data_dict