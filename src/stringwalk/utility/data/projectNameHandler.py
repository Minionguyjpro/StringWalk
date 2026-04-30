from importlib import metadata
from pathlib import Path
import stringwalk


def getProjectName():
    try:
        dist = metadata.distribution("stringwalk")
        return dist.metadata["Name"]
    except metadata.PackageNotFoundError:
        return "StringWalk"

def getProjectNameLower():
    result = getProjectName().lower()
    return result

def getProjectDir():
    return str(Path(stringwalk.__file__).resolve().parent)