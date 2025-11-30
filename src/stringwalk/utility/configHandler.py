from pathlib import Path
from .projectNameHandler import getProjectName
from .jsonParser import writeJson, parseJson
import os
import asyncio

def getConfigPath():
    home = Path.home()
    name = getProjectName()
    if os.name == "nt":  # Windows
        config_dir = Path(os.getenv("APPDATA")) / name
    elif sys.platform == "darwin":  # macOS
        config_dir = home / "Library" / "Application Support" / name
    else:  # Linux / Unix
        config_dir = home / ".config" / name

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"

async def writeConfig(data: dict):
    loop = asyncio.get_running_loop()
    config_file = await loop.run_in_executor(None, getConfigPath)
    
    await asncio.to_thread(writeJson, config_file, data)

async def readConfigItem(key: str):
    loop = asyncio.get_running_loop()
    config_file = await loop.run_in_executor(None, getConfigPath)

    if not config_file.exists:
        await writeConfig({key: default if default is not None else ""})

    data = parseJson(config_file, key)

    return data