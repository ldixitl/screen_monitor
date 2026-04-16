import time
from src.utils.logger_config import setup_logger

logger = setup_logger("sound_manager.log", __name__)


class SoundManager:
    """
    Менеджер звуковых оповещений.
    - Загружает аудиофайлы в зависимости от выбранного региона.
    - Позволяет переключать устройство вывода и регулировать громкость.
    - При отсутствии звуковой системы использует fallback через winsound.
    """

    def __init__(self):
        self.initialized = False
        self.current_region = "Волга"
        self.alarm_sound = None
        self.volume = 0.5
        self.current_device = None  # индекс устройства (int) или None (по умолчанию)
        self._pygame_imported = False  # флаг для ленивого импорта

    @staticmethod
    def get_resource_path(relative_path):
        """
        Возвращает абсолютный путь к ресурсу (для EXE и режима разработки).

        :param relative_path: Относительный путь внутри папки resources.
        :return: Path object с полным путём.
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
        Импортирует pygame и инициализирует mixer, если ещё не сделано.
        Также учитывает текущее выбранное устройство self.current_device.
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
        Устанавливает регион и перезагружает соответствующий звук.

        :param region_name: Название региона (строка).
        """
        self.current_region = region_name
        logger.info(f"Установлен регион: {region_name}")
        self.load_alarm_sound()

    def get_sound_filename(self):
        """
        Возвращает имя файла звука для текущего региона.

        :return: Имя файла.
        """
        sound_mapping = {
            "Волга": "volga_alarm.mp3",
            "Юг": "south_alarm.mp3",
            "Северо-Запад": "north_alarm.mp3",
            "Центр": "centre_alarm.mp3",
            "Москва": "mimo_alarm.mp3",
        }
        return sound_mapping.get(self.current_region, "volga_alarm.mp3")

    def load_alarm_sound(self):
        """
        Загружает звуковой файл для текущего региона.
        При необходимости инициализирует pygame.
        """
        try:
            sound_filename = self.get_sound_filename()
            sound_path = self.get_resource_path(f"sounds/{sound_filename}")

            # Убедимся, что pygame импортирован и mixer инициализирован
            self._ensure_pygame()

            if not sound_path.exists():
                logger.warning(f"Файл {sound_filename} не найден, пробуем звук по умолчанию")
                default_path = self.get_resource_path("sounds/volga_alarm.mp3")
                if default_path.exists():
                    sound_path = default_path
                else:
                    return

            self.alarm_sound = pygame.mixer.Sound(str(sound_path))
            self.alarm_sound.set_volume(self.volume)
            self.initialized = True
            dev_info = f"индекс {self.current_device}" if self.current_device is not None else "по умолчанию"
            logger.info(f"Звук для региона '{self.current_region}' загружен (устройство: {dev_info})")
        except Exception as e:
            logger.error(f"Ошибка загрузки звука: {str(e)}", exc_info=True)
            self.initialized = False

    def set_volume(self, volume):
        """
        Устанавливает громкость (от 0.0 до 1.0).

        :param volume: Значение громкости (float).
        """
        self.volume = max(0.0, min(1.0, volume))
        if self.alarm_sound:
            self.alarm_sound.set_volume(self.volume)
        logger.debug(f"Громкость изменена на {self.volume:.2f}")

    def get_volume(self):
        """
        Возвращает текущую громкость.

        :return: float от 0.0 до 1.0.
        """
        return self.volume

    def get_output_devices(self):
        """
        Возвращает список доступных устройств вывода.

        :return: Список кортежей (индекс, имя устройства).
        """
        # Убедимся, что pygame импортирован (для доступа к _sdl2)
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
        Переключает устройство вывода по индексу.

        :param device_index: Индекс устройства (int) или None (устройство по умолчанию).
        :return: True при успешном переключении, False в противном случае.
        """
        # Если устройство не меняется, ничего не делаем
        if device_index == self.current_device:
            logger.debug(f"Устройство {device_index} уже выбрано, пропускаем переключение")
            return True

        try:
            # Сначала импортируем pygame, если ещё нет
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

            # Завершаем текущий mixer, если он был запущен
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
            logger.error(f"Не удалось переключить устройство на индекс {device_index}: {e}")
            # Восстанавливаем предыдущее устройство
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.quit()
                    time.sleep(0.1)
                if self.current_device is not None:
                    old_names = _sdl2.audio.get_audio_device_names(False)
                    old_name = old_names[self.current_device]
                    pygame.mixer.init(devicename=old_name)
                else:
                    pygame.mixer.init()
                self.load_alarm_sound()
            except Exception as restore_err:
                logger.error(f"Не удалось восстановить предыдущее устройство: {restore_err}")
                # Полный сброс
                if pygame.mixer.get_init():
                    pygame.mixer.quit()
                pygame.mixer.init()
                self.current_device = None
                self.load_alarm_sound()
            return False

    def test_sound(self):
        """Воспроизводит тестовый сигнал (просто вызывает play_alarm)."""
        self.play_alarm()

    def play_alarm(self):
        """
        Воспроизводит звук оповещения (для текущего региона).
        Если звуковая система не готова, используется fallback через winsound.
        """
        # Убедимся, что pygame импортирован и mixer инициализирован, если ещё нет
        if not self._pygame_imported:
            # Если pygame ещё не импортирован, попробуем загрузить звук через load_alarm_sound,
            # который вызовет _ensure_pygame. Но если файл не загружен, то fallback.
            if not self.initialized or not self.alarm_sound:
                logger.warning("Звуковая система не инициализирована, используем winsound")
                self.play_fallback_sound()
                return
            self._ensure_pygame()

        try:
            pygame.mixer.stop()
            self.alarm_sound.play()
            logger.debug(f"Воспроизведение звука для региона: {self.current_region}")
        except Exception as e:
            logger.error(f"Ошибка воспроизведения звука: {str(e)}")
            self.play_fallback_sound()

    @staticmethod
    def play_fallback_sound():
        """
        Запасной вариант звукового оповещения через winsound.Beep.
        Используется, если pygame не может воспроизвести звук.
        """
        try:
            import winsound
            winsound.Beep(400, 500)
            winsound.Beep(600, 200)
            logger.debug("Использован запасной звук (winsound)")
        except Exception as e:
            logger.error(f"Ошибка запасного звука: {str(e)}")


# Глобальный экземпляр менеджера звуков
sound_manager = SoundManager()
