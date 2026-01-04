import json
import os


def load_data():

    full_data = json.load(open("full_data.json", "r", encoding="utf-8"))
    print(f"Initial full data count: {len(full_data)}")
    
    for i in range(1, 18):
        name_file = f"{i}"
        if not os.path.exists(f"poem_full_data_{name_file}.json"):
            print(f"File poem_full_data_{name_file}.json does not exist. Skipping.")
            continue
        poems_data = json.load(open(f"poem_full_data_{name_file}.json", "r", encoding="utf-8"))

        print(f"Loading data from poem_full_data_{name_file}.json with {len(poems_data)} poems.")

        full_data.extend(poems_data)
        print(f"Updated full data count: {len(full_data)} after loading part {name_file}.")


        poems_urls = json.load(open(f"poem_urls_part_{name_file}.json", "r", encoding="utf-8"))

        print(f"Loading URLs from poem_urls_part_{name_file}.json with {len(poems_urls)} URLs.")

        poem_urls_dict = {item["url"]: item for item in poems_urls}

        for poem in poems_data:
            url = poem["url"]
            if url in poem_urls_dict:
                poem_urls_dict.pop(url)

        print(f"Remaining poem URLs count: {len(poem_urls_dict)} after removing crawled poems from part {name_file}.")
        json.dump(list(poem_urls_dict.values()), open(f"poem_urls_part_{name_file}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)


    print(f"Final full data count: {len(full_data)}")
    json.dump(full_data, open("full_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)



if __name__ == "__main__":
    load_data()