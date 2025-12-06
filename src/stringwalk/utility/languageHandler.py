from .configHandler import writeConfigItem

async def setLanguage(lang_code: str):
    await writeConfigItem("lang", lang_code)