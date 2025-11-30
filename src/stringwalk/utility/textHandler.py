from .configHandler import readConfigItem
from pathlib import Path
from .jsonParser import parseJson

async def getText(key: str):
    # Get the current language in the config
    lang = await readConfigItem("lang")

    root = Path(__file__).parent.parent

    json_path = root / "i18n" / f"{lang}/json"

    data = parseJson(json_path, key)

    return data