from pathlib import Path


def getFilenames(path: str, extension: str | None = None) -> list[str]:
    """Get all filenames in a directory, optionally filtering by extension."""
    p = Path(path)
    if not p.is_dir():
        raise ValueError(f"Path {path} is not a directory.")
    
    if extension:
        return [f.stem for f in p.iterdir() if f.is_file() and f.suffix == extension]
    else:
        return [f.name for f in p.iterdir() if f.is_file()]

def getFilenamesJson(path: str) -> list[str]:
    """Get all JSON filenames in a directory."""
    return getFilenames(path, ".json")