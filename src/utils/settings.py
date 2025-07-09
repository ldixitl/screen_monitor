import os

from dotenv import dotenv_values, load_dotenv, set_key


def load_env_settings(env_path):
    """Загружает настройки из .env файла или создает его"""
    if not os.path.exists(env_path):
        default_settings = {
            "INTERVAL": "5",
            "THRESHOLD": "5",
            "EMPTY_THRESHOLD": "99",
            "TELEGRAM_ENABLED": "False",
            "TELEGRAM_TOKEN": "",
            "TELEGRAM_CHAT_ID": "",
        }
        for key, value in default_settings.items():
            set_key(env_path, key, value)

    load_dotenv(env_path)
    return dotenv_values(env_path)


def save_settings(env_path, new_settings):
    """Сохраняет настройки в .env файл"""
    settings_changed = False
    current_settings = dotenv_values(env_path)

    for key, value in new_settings.items():
        if current_settings.get(key) != value:
            set_key(env_path, key, value)
            settings_changed = True

    return settings_changed
