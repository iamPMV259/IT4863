import json


def load_data():
    with open('poem_metadata.json', 'r', encoding='utf-8') as f:
        poems = json.load(f)
        print(f"Loaded {len(poems)} poems from poem_metadata.json")

    poems_dict = {poem['ten_bai']: poem for poem in poems}
    print(f"Created dictionary with {len(poems_dict)} entries")

    poems_diff = [item for item in poems_dict.values()]
    print(f"Converted dictionary back to list with {len(poems_diff)} poems")

    with open('poem_full_data.json', 'w', encoding='utf-8') as f:
        json.dump(poems_diff, f, ensure_ascii=False, indent=4)
        print("Saved poems to poem_full_data.json")

if __name__ == "__main__":
    load_data()
