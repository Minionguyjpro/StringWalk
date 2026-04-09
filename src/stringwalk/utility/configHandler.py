from pathlib import Path
from .data.projectNameHandler import getProjectName
from .jsonParser import writeJson, parseJson
import os
import sys
import json
import asyncio


config_lock = asyncio.Lock()

def getConfigPath(config_file: str | None = "config.json") -> Path:
    """Path to the config."""
    if config_file is None:
        config_file = "config.json"
    
    home = Path.home()
    name = getProjectName()
    if os.name == "nt":  # Windows
        config_dir = Path(os.getenv("APPDATA")) / name
    elif sys.platform == "darwin":  # macOS
        config_dir = home / "Library" / "Application Support" / name
    else:  # Linux / Unix
        config_dir = home / ".config" / name

    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir / config_file

def getDefaultConfigPath() -> Path:
    """Path to your packaged default config."""
    # This file is ../config/config.json relative to THIS file
    root = Path(__file__).resolve().parents[1]
    return root / "config" / "config.json"

async def writeConfig(data: dict[str, object]) -> None:
    config_file = getConfigPath()

    async with config_lock:
        await asyncio.to_thread(writeJson, config_file, **data)

async def writeConfigItem(key: str, value: object, config_file: str | None = "config.json") -> None:
    config_file = getConfigPath(config_file)

    async with config_lock:
        config = await asyncio.to_thread(parseJson, config_file)

        if not isinstance(config, dict):
            config = {}

        config[key] = value
        await asyncio.to_thread(writeJson, config_file, **config)

async def readConfigItem(key: str, default=None, config_file: str | None = "config.json", bootstrap: bool = True) -> object:
    BOOTSTRAP_ALLOWED = {"config.json"}
    
    config_file_str = getConfigPath(config_file)

    should_bootstrap = bootstrap and config_file in BOOTSTRAP_ALLOWED

    # ---- BOOTSTRAP (NO LOCK) ----
    if should_bootstrap and not config_file_str.exists():
        default_config_path = getDefaultConfigPath()

        if default_config_path.exists():
            with open(default_config_path, "r", encoding="utf-8") as f:
                default_config = json.load(f)
        else:
            default_config = {}

        # Create file (no lock yet exists)
        await asyncio.to_thread(writeJson, config_file_str, **default_config)

    # ---- NORMAL READ (LOCKED) ----
    async with config_lock:
        data = await asyncio.to_thread(parseJson, config_file_str, key)

    return data if data is not None else default