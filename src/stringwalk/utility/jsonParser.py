import json
from json import loads

def parseJson(file: str, key: str):
    with open(file) as f:
        data = json.load(f)
        return data.get(key)

def writeJson(file: str, data: dict):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, ident=4)