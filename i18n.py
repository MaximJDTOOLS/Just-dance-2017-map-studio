# i18n.py
STRINGS = {
    "ru": {
        "app_title": "JD2017 Tool — редактор UbiArt",
        "open": "Открыть",
        "save": "Сохранить",
        "export": "Экспорт",
        "timeline": "Таймлайн",
        "picto": "Пиктограммы",
        "gold_move": "Gold Move",
        "actor_editor": "Редактор Actor",
        "songdesc": "SongDesc (isc.ckd)",
        "songdata": "SongData",
        "mainscenes": "MainScenes",
        "ipk_pack": "Упаковать IPK",
        "ipk_unpack": "Распаковать IPK",
        "convert_ps4": "Конвертировать в PS4",
        "menuart": "Создать MenuArt",
        "graph": "Создать Graph",
        "tags": "Метки танца",
        "mashup": "Mashup",
        "on_stage": "On Stage",
        "extreme": "Extreme",
        "alt": "Alt",
        "sweat": "Sweat",
        "preview_video": "Предпросмотр видео",
        "preview_audio": "Предпросмотр аудио",
    },
    "en": {
        "app_title": "JD2017 Tool — UbiArt Editor",
        "open": "Open",
        "save": "Save",
        "export": "Export",
        "timeline": "Timeline",
        "picto": "Pictograms",
        "gold_move": "Gold Move",
        "actor_editor": "Actor Editor",
        "songdesc": "SongDesc (isc.ckd)",
        "songdata": "SongData",
        "mainscenes": "MainScenes",
        "ipk_pack": "Pack IPK",
        "ipk_unpack": "Unpack IPK",
        "convert_ps4": "Convert to PS4",
        "menuart": "Create MenuArt",
        "graph": "Create Graph",
        "tags": "Dance Tags",
        "mashup": "Mashup",
        "on_stage": "On Stage",
        "extreme": "Extreme",
        "alt": "Alt",
        "sweat": "Sweat",
        "preview_video": "Video Preview",
        "preview_audio": "Audio Preview",
    },
}

_current_lang = "ru"

def set_lang(lang: str):
    global _current_lang
    if lang in STRINGS:
        _current_lang = lang

def tr(key: str) -> str:
    return STRINGS.get(_current_lang, STRINGS["en"]).get(key, key)