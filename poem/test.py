import json
import os


def load_poem_data():

    poems = []
    poem_data = json.load(open('poems.json', 'r', encoding='utf-8'))
    print(f"Loaded {len(poem_data)} poems from poems.json")
    poems.extend(poem_data)

    for i in range(2, 8):
        file_path = f"thivien_poems_v{i}.json"
        print(f"Loading poems from {file_path}...")
        if os.path.exists(file_path):
            poem_data_part = json.load(open(file_path, 'r', encoding='utf-8'))
            print(f"Loaded {len(poem_data_part)} poems from {file_path}")
            # You can add further processing here if needed
            poems.extend(poem_data_part)
        else:
            print(f"File {file_path} does not exist. Skipping.")
    print(f"Total poems after loading all parts: {len(poems)}")

    filtered_poems = []
    for poem in poems:
        if poem["author"] and len(poem["poem_content_text"]) > 0:
            filtered_poems.append(poem)

    print(f"Total poems after filtering: {len(filtered_poems)}")

    json.dump(filtered_poems, open('poems.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=4)

if __name__ == "__main__":
    load_poem_data()