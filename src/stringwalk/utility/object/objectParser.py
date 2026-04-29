import json
from pathlib import Path
from ..data.projectNameHandler import getProjectDir


project_dir = getProjectDir()

class ObjectParser:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir or getProjectDir()) / "config"

    def entities(self, extension=".json"):
        path = self.base_dir / "entity"

        return self.return_objects(path, extension)
    
    def return_objects(self, path, extension=None):
        if not path.is_dir():
            raise ValueError(f"{path} is not a valid directory")
    
        return {
            f.stem: json.loads(f.read_text(encoding="utf-8" if f.suffix == ".json" else None))
            for f in path.iterdir()
            if f.is_file() and f.suffix == extension
        }

def getObjects():
    return ObjectParser()