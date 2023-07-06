import json
import os
import glob

def load_all_translations():
    jsons = glob.glob("game_reviews/translations/*.json")
    result = []
    for filename in jsons:
        f = open(filename, encoding="utf8")
        data = json.load(f)
        result.append(data)
    return result

def list_non_uploaded(data):
    result = []
    for d in data:
        if d.get("assume_published") and not(d.get("save_status") and d.get("save_status")=="Page Saved") and not(d.get("content_status") and d.get("content_status")=="Page already has content"):
            result.append(d)
    return result

a = load_all_translations()
b = list_non_uploaded(a)
for json in b:
    print(json.get("name"))

print(len(b))
