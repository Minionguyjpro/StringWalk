from ..configHandler import getConfigPath, readConfigItem, writeConfigItem
from PyQt6.QtCore import Qt


DEFAULT_BINDINGS: dict[str, str] = {
    "jump": "Space",
    "move_left": "A",
    "move_right": "D",
    "pause": "Escape",
}


def _normalize_hotkey_name(value) -> str:
    if value is None:
        return ""

    if isinstance(value, int):
        try:
            key_name = Qt.Key(value).name
            return key_name[4:] if key_name.startswith("Key_") else key_name
        except Exception:
            return str(value)

    text = str(value).strip()
    if not text:
        return text

    if text.isdigit():
        try:
            key_name = Qt.Key(int(text)).name
            return key_name[4:] if key_name.startswith("Key_") else key_name
        except Exception:
            return text

    return text

async def save_bindings(bindings: dict[str, str]):
    """
    Save the given key bindings to the configuration file.
    """
    normalized_bindings = {
        action: _normalize_hotkey_name(key)
        for action, key in bindings.items()
    }

    await writeConfigItem(
        key="hotkeys",
        value=normalized_bindings,
        config_file="controls.json"
    )

async def load_bindings() -> dict[str, str]:
    """
    Load key bindings from the configuration file, or return defaults if not found.
    """
    config_path = getConfigPath("controls.json")

    if not config_path.exists():
        await save_bindings(DEFAULT_BINDINGS)

    bindings = await readConfigItem(
        key="hotkeys",
        default=DEFAULT_BINDINGS,
        config_file="controls.json",
    )

    if not isinstance(bindings, dict):
        bindings = dict(DEFAULT_BINDINGS)

    bindings = {
        action: _normalize_hotkey_name(key)
        for action, key in bindings.items()
    }

    return bindings