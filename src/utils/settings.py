import os

from dotenv import dotenv_values, load_dotenv, set_key


def load_env_settings(env_path: str) -> dict:
    """
    Загружает настройки из .env файла. Если файл отсутствует, создаёт его
    с набором значений по умолчанию.

    :param env_path: Путь к файлу .env.
    :return: Словарь с загруженными настройками.
    """
    if not os.path.exists(env_path):
        default_settings = {
            "INTERVAL": "10",
            "TELEGRAM_ENABLED": "False",
            "TELEGRAM_CHAT_ID": "",
            "WINDOWS_NOTIFICATIONS_ENABLED": "True",
            "MONITOR_LEFT": "11",
            "MONITOR_TOP": "233",
            "MONITOR_WIDTH": "1976",
            "MONITOR_HEIGHT": "220",
            "REGION": "Волга",
            "SOUND_VOLUME": "50",
            "AUDIO_DEVICE": "",
            "CUSTOM_SOUND_VOLGA": "",
            "CUSTOM_SOUND_SOUTH": "",
            "CUSTOM_SOUND_NORTHWEST": "",
            "CUSTOM_SOUND_CENTER": "",
            "CUSTOM_SOUND_MIMO": "",
            "CUSTOM_SOUND_EAST": "",
            "CUSTOM_SOUND_SIBERIA": "",
            "CUSTOM_SOUND_URAL": "",
        }
        for key, value in default_settings.items():
            set_key(env_path, key, value)

    load_dotenv(env_path)
    return dotenv_values(env_path)


def save_settings(env_path: str, new_settings: dict) -> bool:
    """
    Сохраняет новые настройки в .env файл. Записываются только те ключи,
    значения которых изменились по сравнению с текущими.

    :param env_path: Путь к файлу .env.
    :param new_settings: Словарь с новыми настройками (ключ-значение).
    :return: True, если хотя бы одно значение было изменено, иначе False.
    """
    settings_changed = False
    current_settings = dotenv_values(env_path)

    for key, value in new_settings.items():
        if current_settings.get(key) != value:
            set_key(env_path, key, value)
            settings_changed = True

    return settings_changed
