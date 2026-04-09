import json


def parseJson(file: str, *keys):
    try:
        with open(file, "r", encoding="utf-8") as f:
            fdata = json.load(f)

        if not isinstance(fdata, dict):
            print(f"Warning: JSON root is not a dict, got {type(fdata)}")
            return None

        if not keys:
            return fdata

        if len(keys) == 1:
            return fdata.get(keys[0])

        return {k: fdata.get(k) for k in keys}

    except FileNotFoundError:
        print(f"File not found: {file}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON in: {file}")
        return None

def writeJson(file: str, **data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)