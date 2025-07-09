import logging
import os
import sys
from pathlib import Path


def setup_logger(log_filename: str, logger_name: str) -> logging.Logger:
    """
    Создаёт и настраивает логгер с записью в папке 'logs' в корне проекта.

    :param log_filename: Имя файла логов.
    :param logger_name: Название логгера.
    :return: Настроенный объект логгера.
    """
    # Определяем корень проекта (где находится main.py)
    if getattr(sys, 'frozen', False):
        # Для исполняемых файлов (PyInstaller)
        application_path = Path(sys.executable).parent
    else:
        # Для обычного запуска
        application_path = Path(__file__).parent.parent.parent  # Поднимаемся на 3 уровня вверх из src/utils

    logs_dir = os.path.join(application_path, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_file_path = os.path.join(logs_dir, log_filename)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Создаем форматтер
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Обработчик для записи в файл (добавляем, а не перезаписываем)
    file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Если логгер еще не имеет обработчиков - добавляем
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    else:
        # Обновляем обработчики, если они уже есть
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    # Запрещаем распространение логов на корневой логгер
    logger.propagate = False

    return logger
