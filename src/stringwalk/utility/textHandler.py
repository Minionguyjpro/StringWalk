from .configHandler import readConfigItem
from pathlib import Path
from .jsonParser import parseJson


async def getText(keys):
    """
    Get one or multiple translation strings.
    :param keys: str or list of str
    :return: single string if keys is str, or list of strings if keys is list
    """
    single = False
    if isinstance(keys, str):
        keys = [keys]
        single = True
    
    # Get the current language in the config
    lang = await readConfigItem("lang")
    root = Path(__file__).parent.parent

    if lang is None:
        # Set a fallback language in case the config cannot be read
        json_path = root / "i18n" / "en.json"
    else:
        json_path = root / "i18n" / f"{lang}.json"

    results = [parseJson(json_path, key) for key in keys]

    # Return result(s)
    return results