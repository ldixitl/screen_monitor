import numpy as np
from PIL import Image
from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QDesktopWidget, QDialog, QPushButton

from src.utils.logger_config import setup_logger

logger = setup_logger("area_selector.log", __name__)


class AreaSelector(QDialog):
    """
    Диалог для интерактивного выбора области экрана с последующим сохранением координат.
    """

    def __init__(self, parent=None, initial_area=None):
        """
        Инициализирует диалог выбора области.

        :param parent: Родительский виджет (главное окно).
        :param initial_area: Словарь с начальными координатами области
                             (left, top, width, height) — используется при повторном открытии.
        """
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        logger.info("Инициализация селектора области")

        # Прозрачный фон позволяет видеть скриншот под полупрозрачным затемнением
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Охватываем все мониторы одним большим окном
        self.setGeometry(self.get_combined_screen_geometry())

        self.start_point = QPoint()
        self.end_point = QPoint()
        self.selecting = False
        self.selected_area = initial_area or {"left": 11, "top": 233, "width": 1976, "height": 220}

        # Создаём затемнённый снимок экрана в качестве фона
        self.setup_background()

        # Создаём и размещаем кнопки управления
        self.setup_controls()

        logger.debug("Селектор области инициализирован")

    def get_combined_screen_geometry(self) -> QRect:
        """
        Вычисляет прямоугольник, охватывающий все доступные мониторы.

        :return: QRect, объединяющий геометрию всех мониторов.
        """
        desktop = QDesktopWidget()
        total_rect = QRect()
        for i in range(desktop.screenCount()):
            total_rect = total_rect.united(desktop.screenGeometry(i))
        logger.debug(f"Общая геометрия экранов: {total_rect.getRect()}")
        return total_rect

    def setup_background(self):
        """
        Захватывает скриншот всего виртуального экрана, затемняет его
        и сохраняет в `self.background_pixmap` для последующей отрисовки.
        """
        try:
            from mss import mss

            with mss() as sct:
                monitors = sct.monitors
                logger.info(f"Найдено мониторов: {len(monitors) - 1}")
                all_monitors = monitors[0]  # объединённая область всех мониторов

                screenshot = sct.grab(all_monitors)
                logger.debug(f"Захвачен скриншот размером: {screenshot.width}x{screenshot.height}")

                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                darkened = np.array(img) // 2
                darkened_img = Image.fromarray(darkened.astype("uint8"))

                data = darkened_img.tobytes("raw", "RGB")
                qimage = QImage(data, darkened_img.width, darkened_img.height, QImage.Format_RGB888)
                self.background_pixmap = QPixmap.fromImage(qimage)

                logger.debug("Фон сохранён в pixmap")
        except Exception as e:
            logger.error(f"Ошибка создания фона: {str(e)}")

    def setup_controls(self):
        """
        Создаёт кнопки управления (подтверждение, отмена, сброс) и вызывает метод их расположения.
        """
        # Кнопка подтверждения выбора
        self.confirm_btn = QPushButton("Подтвердить выбор", self)
        self.confirm_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4d6bfe;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a5af5;
            }
            QPushButton:disabled {
                background-color: #3a3c42;
                color: #7d7f86;
            }
        """
        )
        self.confirm_btn.clicked.connect(self.accept_selection)
        self.confirm_btn.setEnabled(False)

        # Кнопка отмены (закрывает диалог без сохранения)
        self.cancel_btn = QPushButton("Отмена", self)
        self.cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e55a5a;
            }
        """
        )
        self.cancel_btn.clicked.connect(self.reject)

        # Кнопка сброса к стандартной области (заранее заданные координаты)
        self.reset_btn = QPushButton("Стандартная область", self)
        self.reset_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3a3c42;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4d4f54;
            }
        """
        )
        self.reset_btn.clicked.connect(self.reset_to_default)

        # Размещаем кнопки с учётом количества мониторов
        self.position_controls()

    def position_controls(self):
        """
        Размещает кнопки в правом верхнем углу удобного для пользователя монитора.
        При трёх мониторах кнопки помещаются на центральный (физически), иначе — на правый верх
        всей виртуальной области.
        """
        desktop = QDesktopWidget()
        screen_count = desktop.screenCount()
        margin = 20
        btn_width = 180
        btn_height = 40
        spacing = 50

        total_rect = self.geometry()
        offset_x = total_rect.left()
        offset_y = total_rect.top()

        central_screen_index = -1

        if screen_count == 3:
            # Ищем монитор, содержащий центр всей виртуальной области
            center_x = total_rect.left() + total_rect.width() // 2
            center_y = total_rect.top() + total_rect.height() // 2
            for i in range(screen_count):
                screen_rect = desktop.screenGeometry(i)
                if screen_rect.contains(center_x, center_y):
                    central_screen_index = i
                    break

            if central_screen_index == -1:
                central_screen_index = 1  # fallback

            screen_rect = desktop.screenGeometry(central_screen_index)
            global_x = screen_rect.right() - btn_width - margin
            global_y = screen_rect.top() + margin
            x = global_x - offset_x
            y = global_y - offset_y
        else:
            # По умолчанию — правый верхний угол общей области
            x = self.width() - btn_width - margin
            y = margin

        self.confirm_btn.setGeometry(x, y, btn_width, btn_height)
        self.cancel_btn.setGeometry(x, y + spacing, btn_width, btn_height)
        self.reset_btn.setGeometry(x, y + spacing * 2, btn_width, btn_height)

        # Убеждаемся, что кнопки поверх фона
        self.confirm_btn.raise_()
        self.cancel_btn.raise_()
        self.reset_btn.raise_()

        logger.debug(
            f"Кнопки размещены: screen_count={screen_count}, "
            f"центральный индекс={central_screen_index if screen_count == 3 else 'N/A'}, "
            f"позиция x={x}, y={y}"
        )

    def mousePressEvent(self, event):
        """Обрабатывает начало выделения области."""
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        """Обновляет прямоугольник выделения при движении мыши."""
        if self.selecting:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Завершает выделение, сохраняет координаты и активирует кнопку подтверждения."""
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            self.end_point = event.pos()

            x1 = min(self.start_point.x(), self.end_point.x())
            y1 = min(self.start_point.y(), self.end_point.y())
            x2 = max(self.start_point.x(), self.end_point.x())
            y2 = max(self.start_point.y(), self.end_point.y())

            self.selected_area = {
                "left": x1,
                "top": y1,
                "width": x2 - x1,
                "height": y2 - y1,
            }
            self.confirm_btn.setEnabled(True)
            self.update()

    def paintEvent(self, event):
        """
        Отрисовывает затемнённый фон и поверх него прямоугольник выделения
        с подписью размеров.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Фон
        if self.background_pixmap:
            painter.drawPixmap(self.rect(), self.background_pixmap)

        # Выделение
        if self.selecting or self.selected_area:
            painter.setBrush(QColor(255, 255, 255, 30))

            if self.selecting:
                rect = QRect(self.start_point, self.end_point).normalized()
            else:
                rect = QRect(
                    self.selected_area["left"],
                    self.selected_area["top"],
                    self.selected_area["width"],
                    self.selected_area["height"],
                )

            painter.drawRect(rect)

            # Белая рамка
            pen = QPen(QColor(255, 255, 255), 3, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

            # Текст с размерами
            font = painter.font()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)

            text_rect = QRect(rect.x(), rect.y() - 30, 150, 25)
            painter.fillRect(text_rect, QColor(0, 0, 0, 180))
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(text_rect, Qt.AlignCenter, f"{rect.width()} x {rect.height()}")

        painter.end()

    def accept_selection(self):
        """Подтверждает выбор и закрывает диалог с кодом Accepted."""
        logger.info(f"Выбрана область: {self.selected_area}")
        self.accept()

    def reset_to_default(self):
        """Сбрасывает выделение к стандартной области."""
        self.selected_area = {"left": 11, "top": 233, "width": 1976, "height": 220}
        self.confirm_btn.setEnabled(True)
        self.update()
        logger.info("Установлена стандартная область")

    def get_selected_area(self):
        """Возвращает словарь с координатами выбранной области."""
        return self.selected_area
