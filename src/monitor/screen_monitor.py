import time
import winsound
import cv2
import numpy as np
from mss import mss
from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal
from src.utils.logger_config import setup_logger

logger = setup_logger("monitoring.log", __name__)


class ScreenMonitorThread(QThread):
    change_detected = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Инициализация потока мониторинга экрана")

        # Параметры области захвата экрана
        self.monitor = {"left": 11, "top": 233, "width": 1976, "height": 220}
        self.running = False
        self.check_interval = 5
        self.change_threshold = 5
        self.empty_threshold = 99

        logger.debug(f"Начальные параметры: interval={self.check_interval}s, "
                     f"change_threshold={self.change_threshold}%, "
                     f"empty_threshold={self.empty_threshold}%")

    def run(self):
        """Основной цикл мониторинга экрана"""
        logger.info("Запуск потока мониторинга")
        self.running = True

        try:
            prev_frame = self.capture_screen_area()
            prev_was_empty = self.is_empty_screen(prev_frame)
            logger.debug("Первоначальный кадр захвачен")

            while self.running:
                start_time = time.time()

                try:
                    current_frame = self.capture_screen_area()
                    changed, percent, change_type = self.detect_changes(
                        prev_frame, current_frame, prev_was_empty
                    )

                    if changed:
                        self.handle_change(change_type, percent)

                    prev_frame = current_frame
                    prev_was_empty = self.is_empty_screen(current_frame)

                except Exception as e:
                    logger.error(f"Ошибка в цикле мониторинга: {str(e)}", exc_info=True)
                    self.status_update.emit(f"Ошибка: {str(e)}")
                    time.sleep(5)  # Пауза перед повторной попыткой

                # Корректная пауза с проверкой флага
                elapsed = time.time() - start_time
                if elapsed < self.check_interval:
                    remaining = self.check_interval - elapsed
                    for _ in range(int(remaining * 10)):  # Проверяем флаг каждые 0.1 сек
                        if not self.running:
                            break
                        time.sleep(0.1)

        except Exception as e:
            logger.critical(f"Критическая ошибка в потоке мониторинга: {str(e)}", exc_info=True)
            self.status_update.emit("Критическая ошибка мониторинга")
        finally:
            logger.info("Поток мониторинга остановлен")
            self.running = False

    def handle_change(self, change_type, percent):
        """Обработка обнаруженных изменений"""
        logger.info(f"Обнаружено изменение: {change_type}, процент: {percent:.2f}%")

        if change_type == "appeared":
            message = "🟢 Появилось содержимое на экране!"
            self.change_detected.emit(message)
            winsound.Beep(400, 500)
            winsound.Beep(600, 200)
        elif change_type == "changed":
            message = f"❗ Обнаружены изменения: {percent:.2f}% пикселей"
            self.change_detected.emit(message)
            winsound.Beep(400, 500)
            winsound.Beep(600, 200)
        elif change_type == "disappeared":
            message = "⚪ Экран стал пустым"
            self.change_detected.emit(message)

        logger.debug(f"Отправлено сообщение: {message}")

    def capture_screen_area(self):
        """Захват указанной области экрана"""
        try:
            with mss() as sct:
                screenshot = sct.grab(self.monitor)
                logger.debug(f"Захвачена область: {self.monitor}")
                return Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        except Exception as e:
            logger.error(f"Ошибка захвата экрана: {str(e)}", exc_info=True)
            raise

    def is_empty_screen(self, image):
        """Проверка, является ли экран пустым (белым)"""
        try:
            img_array = np.array(image)
            white_pixels = np.all(img_array == [255, 255, 255], axis=-1)
            white_percent = np.mean(white_pixels) * 100
            logger.debug(f"Процент белых пикселей: {white_percent:.2f}%")
            return white_percent >= self.empty_threshold
        except Exception as e:
            logger.error(f"Ошибка анализа изображения: {str(e)}", exc_info=True)
            raise

    def detect_changes(self, prev_frame, current_frame, prev_was_empty):
        """Обнаружение изменений между кадрами"""
        try:
            current_is_empty = self.is_empty_screen(current_frame)

            if prev_was_empty and not current_is_empty:
                logger.debug("Обнаружено появление содержимого")
                return True, 100, "appeared"
            elif not prev_was_empty and current_is_empty:
                logger.debug("Обнаружено исчезновение содержимого")
                return True, 100, "disappeared"
            elif current_is_empty:
                return False, 0, "empty"

            # Анализ изменений для непустых кадров
            prev_gray = cv2.cvtColor(np.array(prev_frame), cv2.COLOR_RGB2GRAY)
            curr_gray = cv2.cvtColor(np.array(current_frame), cv2.COLOR_RGB2GRAY)

            diff = cv2.absdiff(prev_gray, curr_gray)
            _, threshold = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

            changed_pixels = cv2.countNonZero(threshold)
            total_pixels = diff.shape[0] * diff.shape[1]
            change_percent = (changed_pixels / total_pixels) * 100

            logger.debug(f"Изменено пикселей: {changed_pixels}/{total_pixels} ({change_percent:.2f}%)")

            return change_percent > self.change_threshold, change_percent, "changed"

        except Exception as e:
            logger.error(f"Ошибка детектирования изменений: {str(e)}", exc_info=True)
            raise

    def stop(self):
        """Мгновенная остановка потока"""
        logger.info("Запрошена остановка потока мониторинга")
        self.running = False
        if not self.wait(1000):  # Уменьшил время ожидания до 1 секунды
            logger.warning("Принудительное завершение потока")
            self.terminate()  # Крайняя мера
        logger.debug("Поток успешно остановлен")
