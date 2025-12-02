from pathlib import Path
from .projectNameHandler import getProjectName
from .jsonParser import writeJson, parseJson
import os
import sys
import asyncio

def getConfigPath():
    """Path to the config."""
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

def getDefaultConfigPath():
    """Path to your packaged default config."""
    # This file is ../config/config.json relative to THIS file
    root = Path(__file__).resolve().parents[2]
    return root / "config" / "config.json"

async def writeConfig(data: dict):
    loop = asyncio.get_running_loop()
    config_file = await loop.run_in_executor(None, getConfigPath)
    await asyncio.to_thread(writeJson, config_file, data)

async def readConfigItem(key: str, default=None):
    config_file = getConfigPath()

    if not config_file.exists():
        default_config_path = getDefaultConfigPath()

        if default_config_path.exists():
            with open(default_config_path, "r", encoding="utf-8") as f:
                default_config = json.load(f)

            await writeConfig(default_config)
        else:
            await writeConfig({})

        await asyncio.sleep(0)

    data = parseJson(config_file, key)

    return data if data is not None else default