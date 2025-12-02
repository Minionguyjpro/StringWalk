import json

def parseJson(file: str, key: str = None):
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            print(f"Warning: JSON root is not a dict, got {type(data)}")
            return None
        if key is None:
            return data
        return data.get(key)
    except FileNotFoundError:
        print(f"File not found: {file}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON in: {file}")
        return None

def writeJson(file: str, data: dict):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)