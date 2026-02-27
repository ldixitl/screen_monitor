import time

import numpy as np
from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal

from src.utils.logger_config import setup_logger
from src.utils.sound_manager import sound_manager

logger = setup_logger("monitoring.log", __name__)


class ScreenMonitorThread(QThread):
    """
    Поток для фонового мониторинга заданной области экрана.
    Анализирует изображение, отслеживая появление пикселей заданного цвета (цвет новой аварии)
    При значительном увеличении количества пикселей генерирует сигнал.
    """

    change_detected = pyqtSignal(str)  # Сигнал с сообщением о новой аварии
    status_update = pyqtSignal(str)  # Сигнал для обновления статуса в интерфейсе
    check_completed = pyqtSignal()  # Сигнал, испускаемый после каждой проверки (для таймера)

    def __init__(self, parent=None, monitor_area=None):
        """
        Инициализация потока.

        :param parent: Родительский объект (главное окно).
        :param monitor_area: Словарь с координатами области мониторинга
                             (left, top, width, height). Если не передан, используются значения по умолчанию.
        """
        super().__init__(parent)
        logger.info("Инициализация потока мониторинга экрана")

        # Область захвата (если не задана — берём стандартную)
        self.monitor = monitor_area or {"left": 11, "top": 233, "width": 1976, "height": 220}
        self.running = False
        self.check_interval = 5  # интервал между проверками в секундах

        # Цвет, по которому определяется новая авария (светло-синий, RGB)
        self.new_incident_rgb = (160, 160, 255)

        # Порог увеличения площади цвета (в процентах) для срабатывания
        self.color_increase_threshold = 0.5  # 0.5%

        # Минимальный процент цвета, ниже которого считается шумом
        self.color_min_threshold = 0.1  # 0.1%

        # Предыдущее значение процента цвета (для сравнения)
        self.prev_color_percentage = 0

        logger.debug(
            f"Начальные параметры: interval={self.check_interval}s, "
            f"area={self.monitor}, "
            f"target_color=#{self.new_incident_rgb[0]:02x}{self.new_incident_rgb[1]:02x}{self.new_incident_rgb[2]:02x}"
        )

    def get_color_percentage(self, image):
        """
        Вычисляет процент пикселей заданного цвета в изображении.

        :param image: Объект PIL.Image.
        :return: Процент площади, занятой целевым цветом (float).
        """
        try:
            # Конвертируем PIL Image в numpy array для быстрой обработки
            img_array = np.array(image)

            # Проверяем, что изображение трёхканальное (RGB)
            if img_array.shape[2] != 3:
                return 0

            # Маска пикселей, точно совпадающих с целевым цветом
            target_pixels = np.all(img_array == self.new_incident_rgb, axis=-1)

            total_pixels = img_array.shape[0] * img_array.shape[1]
            color_pixels = np.count_nonzero(target_pixels)

            color_percentage = (color_pixels / total_pixels) * 100

            # Отсекаем шум – очень маленькие значения обнуляем
            if color_percentage < self.color_min_threshold:
                color_percentage = 0

            logger.debug(f"Процент цвета аварий: {color_percentage:.4f}% (пикселей: {color_pixels})")
            return color_percentage

        except Exception as e:
            logger.error(f"Ошибка анализа цвета аварий: {str(e)}", exc_info=True)
            return 0

    def check_color_increase(self, current_percentage):
        """
        Проверяет, произошло ли значительное увеличение процента цвета по сравнению с предыдущим замером.

        :param current_percentage: Текущий процент цвета.
        :return: True, если увеличение превышает порог, иначе False.
        """
        # Игнорируем, если текущий процент ниже порога шума
        if current_percentage < self.color_min_threshold:
            return False

        increase_amount = current_percentage - self.prev_color_percentage
        return increase_amount >= self.color_increase_threshold

    def handle_color_increase(self, percent_increase, total_percentage):
        """
        Обрабатывает событие обнаружения новой аварии: логирует, испускает сигнал и запускает звуковое оповещение.

        :param percent_increase: Величина прироста процента цвета.
        :param total_percentage: Текущий общий процент цвета.
        """
        logger.info(f"Обнаружена новая авария: +{percent_increase:.2f}% (всего: {total_percentage:.2f}%)")
        message = f"🔴 Обнаружена новая авария! (площадь: {total_percentage:.2f}%)"
        self.change_detected.emit(message)

        # Воспроизводим звук через глобальный менеджер звуков
        sound_manager.play_alarm()

        logger.debug(f"Отправлено сообщение: {message}")

    def run(self):
        """
        Основной цикл потока: захват экрана, анализ, пауза.
        Выполняется до тех пор, пока self.running == True.
        """
        logger.info("Запуск потока мониторинга")
        self.running = True

        try:
            # Первый захват для инициализации предыдущего значения
            self.prev_color_percentage = self.get_color_percentage(self.capture_screen_area())
            logger.debug(f"Начальный процент цвета: {self.prev_color_percentage:.4f}%")

            while self.running:
                cycle_start_time = time.time()

                try:
                    current_frame = self.capture_screen_area()
                    current_color_percentage = self.get_color_percentage(current_frame)

                    # Проверяем, произошло ли значительное увеличение цвета
                    if self.check_color_increase(current_color_percentage):
                        increase = current_color_percentage - self.prev_color_percentage
                        self.handle_color_increase(increase, current_color_percentage)

                    # Обновляем предыдущее значение для следующей итерации
                    self.prev_color_percentage = current_color_percentage

                    # Сигнал для обновления таймера в главном окне
                    self.check_completed.emit()

                except Exception as e:
                    logger.error(f"Ошибка в цикле мониторинга: {str(e)}", exc_info=True)
                    self.status_update.emit(f"Ошибка: {str(e)}")
                    time.sleep(5)  # Пауза перед повторной попыткой

                # Вычисляем оставшееся время до следующей проверки
                if self.running:
                    elapsed = time.time() - cycle_start_time
                    sleep_time = max(0, self.check_interval - elapsed)

                    # Дробим паузу на короткие интервалы, чтобы быстро реагировать на остановку потока
                    for _ in range(int(sleep_time * 10)):  # проверка каждые 0.1 сек
                        if not self.running:
                            break
                        time.sleep(0.1)

                    # Оставшиеся доли секунды (если есть)
                    remaining = sleep_time - int(sleep_time)
                    if remaining > 0 and self.running:
                        time.sleep(remaining)

        except Exception as e:
            logger.critical(f"Критическая ошибка в потоке мониторинга: {str(e)}", exc_info=True)
            self.status_update.emit("Критическая ошибка мониторинга")
        finally:
            logger.info("Поток мониторинга остановлен")
            self.running = False

    def capture_screen_area(self):
        """
        Захватывает заданную область экрана с поддержкой нескольких мониторов.

        Поскольку координаты в self.monitor заданы относительно виртуального экрана,
        метод корректирует их, вычитая минимальную левую границу среди всех мониторов.

        :return: Объект PIL.Image с захваченной областью.
        :raises: Любые исключения от mss или PIL, которые затем обрабатываются в run().
        """
        try:
            from mss import mss

            with mss() as sct:
                monitors = sct.monitors[1:]  # пропускаем первый элемент (общая область)

                # Находим самую левую границу всех мониторов
                min_left = min(m["left"] for m in monitors)

                # Корректируем координаты области
                adjusted_area = {
                    "left": self.monitor["left"] + min_left,
                    "top": self.monitor["top"],
                    "width": self.monitor["width"],
                    "height": self.monitor["height"],
                }

                # Пытаемся найти монитор, полностью содержащий скорректированную область
                for monitor in monitors:
                    if (
                        adjusted_area["left"] >= monitor["left"]
                        and adjusted_area["top"] >= monitor["top"]
                        and adjusted_area["left"] + adjusted_area["width"] <= monitor["left"] + monitor["width"]
                        and adjusted_area["top"] + adjusted_area["height"] <= monitor["top"] + monitor["height"]
                    ):
                        screenshot = sct.grab(adjusted_area)
                        logger.debug(f"Захвачена область: {adjusted_area} на мониторе {monitor}")
                        return Image.frombytes("RGB", screenshot.size, screenshot.rgb)

                # Если ни один монитор не подошёл (область выходит за границы), пробуем прямой захват
                logger.warning("Область не найдена на мониторе, используем прямой захват")
                screenshot = sct.grab(adjusted_area)
                return Image.frombytes("RGB", screenshot.size, screenshot.rgb)

        except Exception as e:
            logger.error(f"Ошибка захвата экрана: {str(e)}", exc_info=True)
            raise

    def stop(self):
        """
        Останавливает поток мониторинга.
        Если поток не завершается, принудительно завершает его через terminate().
        """
        logger.info("Запрошена остановка потока мониторинга")
        self.running = False
        if not self.wait(1000):
            logger.warning("Принудительное завершение потока")
            self.terminate()
        logger.debug("Поток успешно остановлен")
