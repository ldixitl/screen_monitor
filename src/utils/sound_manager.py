import shutil
import time
from pathlib import Path

from src.utils.logger_config import setup_logger

logger = setup_logger("sound_manager.log", __name__)


class SoundManager:
    """
    Менеджер звуковых оповещений.
    - Загружает аудиофайлы в зависимости от выбранного региона.
    - Поддерживает пользовательские звуки для каждого региона.
    - Позволяет переключать устройство вывода и регулировать громкость.
    - При отсутствии звуковой системы использует fallback через winsound.
    """

    def __init__(self):
        """
        Инициализирует менеджер звуков, значения громкости и словарь
        пользовательских звуков по регионам.

        :return: None.
        """
        self.initialized = False
        self.current_region = "Волга"
        self.alarm_sound = None
        self.volume = 0.5
        self.current_device = None
        self._pygame_imported = False

        self.custom_sounds = {
            "Волга": "",
            "Юг": "",
            "Северо-Запад": "",
            "Центр": "",
            "Москва": "",
            "Дальний Восток": "",
            "Сибирь": "",
            "Урал": "",
        }

    @staticmethod
    def get_resource_path(relative_path):
        """
        Возвращает абсолютный путь к ресурсу для EXE и режима разработки.

        :param relative_path: Относительный путь внутри папки resources.
        :return: Полный путь к ресурсу.
        """
        import sys
        from pathlib import Path

        if getattr(sys, "frozen", False):
            if hasattr(sys, "_MEIPASS"):
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(sys.executable).parent
        else:
            base_path = Path(__file__).parent.parent.parent

        return base_path / "resources" / relative_path

    def _ensure_pygame(self):
        """
        Импортирует pygame и инициализирует mixer при первом обращении.

        :return: None.
        """
        if not self._pygame_imported:
            global pygame, _sdl2
            import pygame
            from pygame import _sdl2

            self._pygame_imported = True

        if not pygame.mixer.get_init():
            if self.current_device is not None:
                names = _sdl2.audio.get_audio_device_names(False)
                dev_name = names[self.current_device]
                pygame.mixer.init(devicename=dev_name)
            else:
                pygame.mixer.init()
            logger.debug("Pygame mixer инициализирован")

    def set_region(self, region_name):
        """
        Устанавливает текущий регион и перезагружает соответствующий звук.

        :param region_name: Название региона.
        :return: None.
        """
        self.current_region = region_name
        logger.info(f"Установлен регион: {region_name}")
        self.load_alarm_sound()

    def load_custom_sounds_from_settings(self, settings: dict):
        """
        Загружает пользовательские пути к звукам из словаря настроек.

        :param settings: Словарь настроек, загруженный из .env.
        :return: None.
        """
        self.custom_sounds = {
            "Волга": settings.get("CUSTOM_SOUND_VOLGA", "") or "",
            "Юг": settings.get("CUSTOM_SOUND_SOUTH", "") or "",
            "Северо-Запад": settings.get("CUSTOM_SOUND_NORTHWEST", "") or "",
            "Центр": settings.get("CUSTOM_SOUND_CENTER", "") or "",
            "Москва": settings.get("CUSTOM_SOUND_MIMO", "") or "",
            "Дальний Восток": settings.get("CUSTOM_SOUND_EAST", "") or "",
            "Сибирь": settings.get("CUSTOM_SOUND_SIBERIA", "") or "",
            "Урал": settings.get("CUSTOM_SOUND_URAL", "") or "",
        }
        logger.debug(f"Пользовательские звуки загружены: {self.custom_sounds}")

    def set_custom_sound(self, region_name: str, file_path: str):
        """
        Копирует пользовательский аудиофайл в папку resources/user_sounds
        и устанавливает его для указанного региона.

        :param region_name: Название региона.
        :param file_path: Путь к исходному аудиофайлу.
        :return: None.
        """
        if region_name not in self.custom_sounds:
            logger.warning(f"Неизвестный регион для установки звука: {region_name}")
            return

        source_path = Path(file_path)
        if not source_path.exists() or not source_path.is_file():
            logger.warning(f"Файл пользовательского звука не найден: {file_path}")
            return

        try:
            old_path = self.custom_sounds.get(region_name, "").strip()

            user_sounds_dir = self.get_user_sounds_dir()
            extension = source_path.suffix.lower() or ".mp3"
            target_name = f"{self.get_region_sound_basename(region_name)}_custom{extension}"
            target_path = user_sounds_dir / target_name

            shutil.copy2(source_path, target_path)
            self.custom_sounds[region_name] = str(target_path)

            if old_path:
                try:
                    old_file = Path(old_path)
                    if old_file.exists() and old_file.is_file() and old_file.resolve() != target_path.resolve():
                        if user_sounds_dir.resolve() in old_file.resolve().parents:
                            old_file.unlink()
                except Exception as cleanup_error:
                    logger.error(
                        f"Ошибка при удалении старой копии звука для региона '{region_name}': {cleanup_error}",
                        exc_info=True,
                    )

            logger.info(f"Для региона '{region_name}' установлен пользовательский звук: {target_path}")

            if self.current_region == region_name:
                self.load_alarm_sound()

        except Exception as e:
            logger.error(
                f"Ошибка при копировании пользовательского звука для региона '{region_name}': {e}",
                exc_info=True,
            )

    def clear_custom_sound(self, region_name: str):
        """
        Сбрасывает пользовательский звук региона на встроенный стандартный.

        :param region_name: Название региона.
        :return: None.
        """
        if region_name not in self.custom_sounds:
            logger.warning(f"Неизвестный регион для сброса звука: {region_name}")
            return

        self.custom_sounds[region_name] = ""
        logger.info(f"Для региона '{region_name}' пользовательский звук сброшен")

        if self.current_region == region_name:
            try:
                if self._pygame_imported:
                    if pygame.mixer.get_init():
                        pygame.mixer.stop()
                self.alarm_sound = None
            except Exception as e:
                logger.error(f"Ошибка при остановке текущего звука: {e}", exc_info=True)

            self.load_alarm_sound()

    def get_builtin_sound_filename(self):
        """
        Возвращает имя встроенного звукового файла для текущего региона.

        :return: Имя файла встроенного звука.
        """
        sound_mapping = {
            "Волга": "volga_alarm.mp3",
            "Юг": "south_alarm.mp3",
            "Северо-Запад": "north_alarm.mp3",
            "Центр": "centre_alarm.mp3",
            "Москва": "mimo_alarm.mp3",
            "Дальний Восток": "east_alarm.mp3",
            "Сибирь": "siberia_alarm.mp3",
            "Урал": "ural_alarm.mp3",
        }
        return sound_mapping.get(self.current_region, "volga_alarm.mp3")

    def get_user_sounds_dir(self) -> Path:
        """
        Возвращает путь к папке пользовательских звуков внутри resources.
        При отсутствии папки создаёт её.

        :return: Путь к папке resources/user_sounds.
        """
        user_sounds_dir = self.get_resource_path("user_sounds")
        user_sounds_dir.mkdir(parents=True, exist_ok=True)
        return user_sounds_dir

    def get_region_sound_basename(self, region_name: str) -> str:
        """
        Возвращает безопасовое базовое имя файла для региона.

        :param region_name: Название региона.
        :return: Базовое имя файла без расширения.
        """
        mapping = {
            "Волга": "volga",
            "Юг": "south",
            "Северо-Запад": "northwest",
            "Центр": "center",
            "Москва": "mimo",
            "Дальний Восток": "east",
            "Сибирь": "siberia",
            "Урал": "ural",
        }
        return mapping.get(region_name, "custom_sound")

    def get_sound_path(self) -> Path | None:
        """
        Возвращает путь к звуку для текущего региона. Сначала проверяет
        пользовательский файл, затем встроенный ресурс.

        :return: Путь к звуковому файлу или None, если ничего не найдено.
        """
        custom_path = self.custom_sounds.get(self.current_region, "").strip()

        if custom_path:
            custom_file = Path(custom_path)
            if custom_file.exists() and custom_file.is_file():
                logger.debug(f"Используется пользовательский звук: {custom_file}")
                return custom_file
            logger.warning(f"Пользовательский звук для региона '{self.current_region}' не найден: {custom_path}")

        builtin_filename = self.get_builtin_sound_filename()
        builtin_path = self.get_resource_path(f"sounds/{builtin_filename}")

        if builtin_path.exists():
            logger.debug(f"Используется встроенный звук: {builtin_path}")
            return builtin_path

        logger.warning(f"Встроенный звук не найден: {builtin_filename}")

        default_path = self.get_resource_path("sounds/volga_alarm.mp3")
        if default_path.exists():
            logger.warning("Используется резервный встроенный звук volga_alarm.mp3")
            return default_path

        return None

    def load_alarm_sound(self):
        """
        Загружает звуковой файл для текущего региона. Приоритет отдаётся
        пользовательскому файлу, если он существует.

        :return: None.
        """
        try:
            sound_path = self.get_sound_path()
            if sound_path is None:
                logger.error("Не найден ни пользовательский, ни встроенный звуковой файл")
                self.initialized = False
                self.alarm_sound = None
                return

            self._ensure_pygame()

            self.alarm_sound = pygame.mixer.Sound(str(sound_path))
            self.alarm_sound.set_volume(self.volume)
            self.initialized = True

            dev_info = f"индекс {self.current_device}" if self.current_device is not None else "по умолчанию"
            logger.info(f"Звук для региона '{self.current_region}' загружен: {sound_path} (устройство: {dev_info})")
        except Exception as e:
            logger.error(f"Ошибка загрузки звука: {str(e)}", exc_info=True)
            self.initialized = False
            self.alarm_sound = None

    def set_volume(self, volume):
        """
        Устанавливает громкость воспроизведения в диапазоне от 0.0 до 1.0.

        :param volume: Значение громкости.
        :return: None.
        """
        self.volume = max(0.0, min(1.0, volume))
        if self.alarm_sound:
            self.alarm_sound.set_volume(self.volume)
        logger.debug(f"Громкость изменена на {self.volume:.2f}")

    def get_volume(self):
        """
        Возвращает текущую громкость.

        :return: Текущее значение громкости.
        """
        return self.volume

    def get_output_devices(self):
        """
        Возвращает список доступных устройств вывода звука.

        :return: Список кортежей вида (индекс, имя устройства).
        """
        if not self._pygame_imported:
            global pygame, _sdl2
            import pygame
            from pygame import _sdl2

            self._pygame_imported = True

        devices = []
        try:
            names = _sdl2.audio.get_audio_device_names(False)
            for idx, name in enumerate(names):
                devices.append((idx, name))
            logger.debug(f"Найдено устройств вывода: {len(devices)}")
        except Exception as e:
            logger.error(f"Ошибка получения списка устройств: {e}", exc_info=True)
        return devices

    def set_device_by_index(self, device_index):
        """
        Переключает устройство вывода звука по его индексу.

        :param device_index: Индекс устройства или None для устройства по умолчанию.
        :return: True при успешном переключении, иначе False.
        """
        if device_index == self.current_device:
            logger.debug(f"Устройство {device_index} уже выбрано, пропускаем переключение")
            return True

        try:
            if not self._pygame_imported:
                global pygame, _sdl2
                import pygame
                from pygame import _sdl2

                self._pygame_imported = True

            if device_index is not None:
                names = _sdl2.audio.get_audio_device_names(False)
                if device_index < 0 or device_index >= len(names):
                    logger.error(f"Индекс устройства {device_index} вне диапазона")
                    return False
                dev_name = names[device_index]
            else:
                dev_name = None

            if pygame.mixer.get_init():
                pygame.mixer.quit()
                time.sleep(0.1)

            if dev_name is not None:
                pygame.mixer.init(devicename=dev_name)
                self.current_device = device_index
            else:
                pygame.mixer.init()
                self.current_device = None

            self.load_alarm_sound()
            logger.info(f"Устройство вывода изменено на индекс {device_index}")
            return True

        except Exception as e:
            logger.error(f"Не удалось переключить устройство на индекс {device_index}: {e}", exc_info=True)
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.quit()
                    time.sleep(0.1)
                pygame.mixer.init()
                self.current_device = None
                self.load_alarm_sound()
            except Exception as restore_error:
                logger.error(f"Ошибка восстановления звуковой системы: {restore_error}", exc_info=True)
            return False

    def test_sound(self):
        """
        Воспроизводит тестовый сигнал для текущего региона.

        :return: None.
        """
        self.play_alarm()

    def play_alarm(self):
        """
        Воспроизводит текущий сигнал тревоги. При ошибке использует fallback.

        :return: None.
        """
        if not self.initialized or not self.alarm_sound:
            logger.warning("Звуковая система не инициализирована, используем winsound")
            self.play_fallback_sound()
            return

        try:
            pygame.mixer.stop()
            self.alarm_sound.play()
            logger.debug(f"Воспроизведение звука для региона: {self.current_region}")
        except Exception as e:
            logger.error(f"Ошибка воспроизведения звука: {str(e)}", exc_info=True)
            self.play_fallback_sound()

    @staticmethod
    def play_fallback_sound():
        """
        Воспроизводит резервный звуковой сигнал через winsound.

        :return: None.
        """
        try:
            import winsound

            winsound.Beep(400, 500)
            winsound.Beep(600, 200)
            logger.debug("Использован запасной звук (winsound)")
        except Exception as e:
            logger.error(f"Ошибка запасного звука: {str(e)}", exc_info=True)

    def stop_alarm(self):
        """
        Останавливает текущее воспроизведение звука.

        :return: None.
        """
        if self.initialized:
            try:
                pygame.mixer.stop()
                logger.debug("Воспроизведение звука остановлено")
            except Exception as e:
                logger.error(f"Ошибка остановки звука: {str(e)}", exc_info=True)


sound_manager = SoundManager()
