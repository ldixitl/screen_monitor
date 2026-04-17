from pathlib import Path

from PyQt5.QtCore import QPropertyAnimation, Qt, QTimer, pyqtProperty
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (QComboBox, QDialog, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPushButton,
                             QSlider, QStyle, QToolButton, QVBoxLayout, QWidget)

from src.utils.logger_config import setup_logger

logger = setup_logger("widgets.log", __name__)


class RoundedGroupBox(QGroupBox):
    """
    Группа с закруглёнными углами и тёмным фоном, используемая для визуального
    выделения блоков настроек в интерфейсе.
    """

    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setStyleSheet(
            """
            QGroupBox {
                background-color: #212327;
                border: 1px solid #3a3c42;
                border-radius: 12px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                background-color: #212327;
                color: #f8faff;
                font-weight: bold;
            }
        """
        )


class StyledButton(QPushButton):
    """
    Кастомная кнопка с единым стилем для всего приложения:
    синий фон, скруглённые углы, изменение цвета при наведении.
    """

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(36)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #4d6bfe;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3a5af5;
            }
            QPushButton:pressed {
                background-color: #2d4de3;
            }
            QPushButton:disabled {
                background-color: #3a3c42;
                color: #7d7f86;
            }
        """
        )


class TitleBar(QWidget):
    """
    Кастомная строка заголовка для frameless-окон.
    Содержит иконку, название, кнопки «О программе», свернуть и закрыть.
    Обеспечивает перетаскивание окна за эту область.
    """

    @staticmethod
    def get_resource_path(relative_path):
        """Возвращает абсолютный путь к ресурсу (для EXE и режима разработки)."""
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

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(46)
        self.setStyleSheet("background-color: #292a2d;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 2, 12, 2)
        layout.setSpacing(10)

        # Иконка приложения (или стандартная, если файл не найден)
        self.icon_label = QLabel()
        icon_path = self.get_resource_path("icons/app_icon.png")
        if icon_path.exists():
            self.icon_label.setPixmap(QIcon(str(icon_path)).pixmap(32, 32))
        else:
            self.icon_label.setPixmap(QIcon(self.style().standardIcon(QStyle.SP_ComputerIcon)).pixmap(32, 32))
        layout.addWidget(self.icon_label)

        # Название программы
        self.title = QLabel("Screen Monitor")
        self.title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.title.setStyleSheet("color: #f8faff;")
        layout.addWidget(self.title)

        layout.addStretch()

        # Кнопка вызова окна «О программе»
        self.about_btn = QToolButton()
        self.about_btn.setText("?")
        self.about_btn.setToolTip("О программе")
        self.about_btn.setStyleSheet(
            """
            QToolButton {
                background-color: transparent;
                color: #7d7f86;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QToolButton:hover {
                color: #4d6bfe;
                background-color: #3a3c42;
                border-radius: 4px;
            }
        """
        )
        self.about_btn.setFixedSize(24, 24)
        self.about_btn.clicked.connect(self.show_about_dialog)
        layout.addWidget(self.about_btn)

        # Кнопка сворачивания окна
        self.minimize_btn = QToolButton()
        self.minimize_btn.setIcon(QIcon(self.style().standardIcon(QStyle.SP_TitleBarMinButton)))
        self.minimize_btn.setToolTip("Свернуть")
        self.minimize_btn.setStyleSheet(
            """
            QToolButton {
                background-color: transparent;
                border: none;
            }
            QToolButton:hover {
                background-color: #3a3c42;
                border-radius: 4px;
            }
        """
        )
        self.minimize_btn.setFixedSize(24, 24)
        self.minimize_btn.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.minimize_btn)

        # Кнопка закрытия окна
        self.close_btn = QToolButton()
        self.close_btn.setIcon(QIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton)))
        self.close_btn.setStyleSheet(
            """
            QToolButton {
                background-color: transparent;
                border: none;
            }
            QToolButton:hover {
                background-color: #ff5f57;
            }
        """
        )
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.parent.close)
        layout.addWidget(self.close_btn)

    def show_about_dialog(self):
        """Показывает модальное окно с информацией о программе."""
        try:
            about_text = """
            <div style="font-family: 'Segoe UI';">
            <h2 style="color: #4d6bfe; text-align: center;">Screen Monitor</h2>

            <p><b>Версия:</b> 1.1.0</p>
            <p><b>Описание:</b> Программа для мониторинга экрана и обнаружения аварийных ситуаций в системах БТИ.</p>

            <h3>Основные функции:</h3>
            <ul>
                <li>Мониторинг выбранной области экрана</li>
                <li>Обнаружение новых аварий</li>
                <li>Звуковые оповещения для разных регионов</li>
                <li>Telegram-уведомления через бота @monitoringbti_bot</li>
                <li>Всплывающие Windows-уведомления</li>
                <li>Гибкая настройка интервала проверки</li>
            </ul>

            <h3>Как использовать:</h3>
            <ol>
                <li>Выберите область мониторинга с помощью кнопки "Выбрать область"</li>
                <li>Настройте интервал проверки (рекомендуется 10-20 секунд)</li>
                <li>Получите Telegram ID через бота @monitoringbti_bot</li>
                <li>Включите нужные типы уведомлений</li>
                <li>Нажмите "Запустить мониторинг"</li>
            </ol>

            <h3>Поддерживаемые регионы:</h3>
            <ul>
                <li>Волга</li>
                <li>Юг</li>
                <li>Северо-Запад</li>
                <li>Центр</li>
                <li>Москва</li>
            </ul>

            <p><b>Для получения Telegram ID:</b><br>
            Перейдите к <a href='https://t.me/monitoringbti_bot' style='color: #4d6bfe;'>@monitoringbti_bot</a> и нажмите "Получить ID"</p>

            <hr style="border: 1px solid #3a3c42;">
            <p style="color: #7d7f86; font-size: 10px; text-align: center;">
            © 2026 Screen Monitor<br>
            Gendin N. S.
            </p>
            </div>
            """

            msg_box = QMessageBox(self.parent)
            msg_box.setWindowTitle("О программе - Screen Monitor")
            msg_box.setTextFormat(Qt.RichText)
            msg_box.setText(about_text)

            icon_path = self.get_resource_path("icons/app_icon.png")
            if icon_path.exists():
                msg_box.setWindowIcon(QIcon(str(icon_path)))

            msg_box.setStyleSheet(
                """
                QMessageBox {
                    background-color: #292a2d;
                    color: #f8faff;
                    font-family: 'Segoe UI';
                }
                QMessageBox QLabel {
                    color: #f8faff;
                    background-color: transparent;
                    font-family: 'Segoe UI';
                }
                QMessageBox QPushButton {
                    background-color: #4d6bfe;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                    min-width: 100px;
                    font-family: 'Segoe UI';
                    font-weight: bold;
                }
                QMessageBox QPushButton:hover {
                    background-color: #3a5bd0;
                }
            """
            )

            msg_box.exec_()

        except Exception as e:
            logger.error(f"Ошибка при показе окна 'О программе': {str(e)}")

    def mousePressEvent(self, event):
        """
        Запоминает позицию курсора относительно окна для последующего перетаскивания.
        """
        if event.button() == Qt.LeftButton:
            self.parent.drag_position = event.globalPos() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """
        Перемещает главное окно при зажатой левой кнопке мыши.
        """
        if event.buttons() == Qt.LeftButton:
            self.parent.move(event.globalPos() - self.parent.drag_position)
            event.accept()


class NotificationWidget(QWidget):
    """
    Всплывающее уведомление поверх всех окон в стиле диалога настроек.
    Содержит заголовок с мигающей красной точкой, текст сообщения и кнопку закрытия.
    Автоматически закрывается через заданное время.
    """

    def __init__(self, message, parent=None, duration=15, title="Уведомление"):
        super().__init__(parent)
        logger.debug(f"Создание NotificationWidget: {message[:50]}")

        self.duration = duration
        self.dot_visible = True

        # Убираем стандартную рамку, делаем фон полупрозрачным для скруглённых углов
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(400, 170)

        # Внешний слой с отступом 1px для имитации тонкой рамки
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(1, 1, 1, 1)
        outer_layout.setSpacing(0)

        # Основной контейнер с фоном и рамкой (как в SoundSettingsDialog)
        self.container = QWidget()
        self.container.setObjectName("notificationContainer")
        self.container.setStyleSheet(
            """
            #notificationContainer {
                background-color: #292a2d;
                border: 1px solid #4d6bfe;
                border-radius: 10px;
            }
        """
        )
        outer_layout.addWidget(self.container)

        # Внутренний layout контейнера
        inner_layout = QVBoxLayout(self.container)
        inner_layout.setContentsMargins(20, 15, 20, 15)
        inner_layout.setSpacing(12)

        # Заголовок с центрированной красной точкой
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)
        header_layout.setAlignment(Qt.AlignCenter)

        self.dot_label = QLabel("●")
        self.dot_label.setStyleSheet("color: #ff3b3b; font-size: 18px;")
        self.dot_label.setFixedWidth(16)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #4d6bfe;")

        header_layout.addWidget(self.dot_label)
        header_layout.addWidget(title_label)
        inner_layout.addLayout(header_layout)

        # Текст сообщения
        message_label = QLabel(message)
        message_label.setStyleSheet(
            "color: #f8faff; font-size: 11px; background-color: #3a3c42; padding: 8px; border-radius: 6px;"
        )
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setMinimumHeight(40)
        inner_layout.addWidget(message_label)

        # Кнопка закрытия
        confirm_btn = QPushButton("Принято")
        confirm_btn.setMinimumHeight(40)
        confirm_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4d6bfe;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #3a5af5;
            }
        """
        )
        confirm_btn.clicked.connect(self.close)
        inner_layout.addWidget(confirm_btn)

        self.setWindowOpacity(0.98)

        # Таймер автоматического закрытия
        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.close)
        self.auto_close_timer.start(self.duration * 1000)

        # Анимация пульсации рамки (alpha от 80 до 255)
        self.pulse_animation = QPropertyAnimation(self, b"borderOpacity")
        self.pulse_animation.setDuration(900)
        self.pulse_animation.setStartValue(80)
        self.pulse_animation.setEndValue(255)
        self.pulse_animation.setLoopCount(-1)

        # Таймер мигания красной точки
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.toggle_dot)
        self.blink_timer.start(500)

        logger.debug("NotificationWidget создан")

    def toggle_dot(self):
        """Переключает внешний вид красной точки: яркость и размер меняются для эффекта пульса."""
        self.dot_visible = not self.dot_visible
        if self.dot_visible:
            self.dot_label.setStyleSheet("color: #ff3b3b; font-size: 18px;")
        else:
            self.dot_label.setStyleSheet("color: #660000; font-size: 16px;")

    def set_border_opacity(self, opacity):
        """
        Устанавливает прозрачность рамки контейнера.
        :param opacity: целое число от 0 до 255.
        """
        self.container.setStyleSheet(
            f"""
            #notificationContainer {{
                background-color: #292a2d;
                border: 1px solid rgba(77, 107, 254, {opacity});
                border-radius: 10px;
            }}
        """
        )

    def get_border_opacity(self):
        """Возвращает текущую прозрачность рамки (нужно для свойства)."""
        return 255  # не используется в анимации, но требуется для свойства

    borderOpacity = pyqtProperty(float, fget=get_border_opacity, fset=set_border_opacity)

    def showEvent(self, event):
        super().showEvent(event)
        self.raise_()
        self.activateWindow()

        # Плавное появление (fade-in)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(350)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(0.98)
        self.fade_animation.start()

        # Запуск пульсации рамки
        self.pulse_animation.start()

        logger.debug("NotificationWidget показан с анимациями")

    def closeEvent(self, event):
        self.blink_timer.stop()
        self.pulse_animation.stop()
        super().closeEvent(event)
        logger.debug("NotificationWidget закрыт")


class SoundSettingsDialog(QDialog):
    """
    Диалог настройки звука: выбор устройства вывода, регулировка громкости,
    тестовое воспроизведение. Оформлен в едином стиле с главным окном.
    """

    @staticmethod
    def get_resource_path(relative_path):
        """Возвращает абсолютный путь к ресурсу (для EXE и разработки)."""
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

    def __init__(self, sound_manager, parent=None):
        super().__init__(parent)

        # Убираем стандартную рамку, делаем фон полупрозрачным для скруглённых углов
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(410, 460)

        self.sound_manager = sound_manager
        self.original_volume = sound_manager.get_volume()
        self.original_device = sound_manager.current_device
        self.original_custom_sounds = dict(sound_manager.custom_sounds)
        self._accepted = False

        if parent and hasattr(parent, "region_combo"):
            self.current_region = parent.region_combo.currentText()
        else:
            self.current_region = sound_manager.current_region

        # Внешний слой с отступом в 1px для имитации тонкой рамки
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(1, 1, 1, 1)
        outer_layout.setSpacing(0)

        # Основной контейнер с фоном и рамкой
        self.container = QWidget()
        self.container.setObjectName("dialogContainer")
        self.container.setStyleSheet(
            """
            #dialogContainer {
                background-color: #292a2d;
                border: 1px solid #4d6bfe;
                border-radius: 10px;
            }
        """
        )
        outer_layout.addWidget(self.container)

        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Встраиваем тот же TitleBar, но скрываем ненужные кнопки
        self.title_bar = TitleBar(self)
        self.title_bar.title.setText("Настройки звука")
        self.title_bar.about_btn.hide()
        self.title_bar.minimize_btn.hide()
        self.title_bar.close_btn.clicked.disconnect()
        self.title_bar.close_btn.clicked.connect(self.reject)
        main_layout.addWidget(self.title_bar)

        # Контентная область
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 15, 20, 15)
        content_layout.setSpacing(12)

        # Блок громкости (слайдер + иконка)
        vol_container = QWidget()
        vol_container.setStyleSheet("background-color: #32343a; border-radius: 8px;")
        vol_layout = QHBoxLayout(vol_container)
        vol_layout.setSpacing(10)

        self.volume_icon_label = QLabel()
        self.volume_icon_label.setFixedSize(24, 24)
        self.volume_icon_label.setScaledContents(True)
        vol_layout.addWidget(self.volume_icon_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.original_volume * 100))
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        self.volume_slider.setTracking(True)
        self.volume_slider.setSingleStep(1)
        self.volume_slider.setPageStep(5)
        self.volume_slider.setMinimumHeight(30)

        self.volume_slider.setStyleSheet(
            """
            QSlider::groove:horizontal {
                height: 8px;
                background: #32343a;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                border-radius: 4px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5d7aff, stop:1 #8ab2ff);
            }
            QSlider::add-page:horizontal {
                background: #2b2d31;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 3px solid #4d6bfe;
                width: 18px;
                height: 18px;
                border-radius: 9px;
                margin: -5px 0;
            }
            QSlider::handle:horizontal:hover {
                border: 3px solid #7aa2f7;
            }
            QSlider::handle:horizontal:pressed {
                border: 3px solid #3a5af5;
            }
        """
        )
        vol_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel(f"{self.volume_slider.value()}%")
        self.volume_label.setFixedWidth(35)
        self.volume_label.setStyleSheet("color: #f8faff;")
        vol_layout.addWidget(self.volume_label)

        content_layout.addWidget(vol_container)

        # Выбор устройства вывода
        dev_layout = QHBoxLayout()
        dev_layout.addWidget(QLabel("Устройство:"))

        self.device_combo = QComboBox()
        self.device_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #3a3c42;
                color: #f8faff;
                border: 1px solid #4d6bfe;
                border-radius: 6px;
                padding: 5px;
                min-height: 28px;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3c42;
                color: #f8faff;
                selection-background-color: #4d6bfe;
                border: 1px solid #4d6bfe;
            }
        """
        )
        self.populate_devices()
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        dev_layout.addWidget(self.device_combo)
        content_layout.addLayout(dev_layout)

        # Блок пользовательского звука для текущего региона
        sound_file_container = QWidget()
        sound_file_container.setStyleSheet("background-color: #32343a; border-radius: 8px;")
        sound_file_layout = QVBoxLayout(sound_file_container)
        sound_file_layout.setContentsMargins(12, 10, 12, 10)
        sound_file_layout.setSpacing(8)

        region_label = QLabel(f"Сигнал для региона: {self.current_region}")
        region_label.setStyleSheet("color: #f8faff; font-weight: bold;")
        sound_file_layout.addWidget(region_label)

        self.custom_sound_path_label = QLabel()
        self.custom_sound_path_label.setWordWrap(True)
        self.custom_sound_path_label.setStyleSheet(
            """
            color: #b5b7be;
            background-color: #2b2d31;
            border-radius: 6px;
            padding: 8px;
            """
        )
        sound_file_layout.addWidget(self.custom_sound_path_label)

        sound_buttons_layout = QHBoxLayout()
        sound_buttons_layout.setSpacing(8)

        self.choose_sound_btn = QPushButton("Выбрать звук")
        self.choose_sound_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3a3c42;
                color: #f8faff;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4d6bfe;
            }
            """
        )
        self.choose_sound_btn.clicked.connect(self.choose_custom_sound)
        sound_buttons_layout.addWidget(self.choose_sound_btn)

        self.reset_sound_btn = QPushButton("Сбросить")
        self.reset_sound_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3a3c42;
                color: #f8faff;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
            """
        )
        self.reset_sound_btn.clicked.connect(self.reset_custom_sound)
        sound_buttons_layout.addWidget(self.reset_sound_btn)

        sound_file_layout.addLayout(sound_buttons_layout)
        content_layout.addWidget(sound_file_container)

        # Кнопка тестового сигнала
        test_btn = QPushButton("Тестовый сигнал")
        test_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4d6bfe;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3a5af5; }
            QPushButton:pressed { background-color: #2d4de3; }
        """
        )
        test_btn.clicked.connect(self.test_sound)
        content_layout.addWidget(test_btn)

        # Кнопки OK/Отмена
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(test_btn.styleSheet())
        ok_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet(test_btn.styleSheet())
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        content_layout.addLayout(btn_layout)

        main_layout.addWidget(content_widget)

        # Центрирование относительно родительского окна
        if parent:
            parent_rect = parent.geometry()
            self.move(parent_rect.center() - self.rect().center())

        self.update_volume_icon(self.volume_slider.value())
        self.update_custom_sound_label()

    def update_volume_icon(self, value):
        """
        Обновляет иконку громкости в зависимости от текущего значения (0, низкая, средняя, высокая).
        """
        if value == 0:
            icon_name = "volume_off.png"
        elif value <= 32:
            icon_name = "volume_low.png"
        elif value <= 65:
            icon_name = "volume_medium.png"
        else:
            icon_name = "volume_high.png"

        icon_path = self.get_resource_path(f"icons/{icon_name}")
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            scaled = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.volume_icon_label.setPixmap(scaled)
        else:
            # fallback на текстовый символ
            self.volume_icon_label.setText("🔊")
            self.volume_icon_label.setStyleSheet("color: #f8faff; font-size: 16px;")

    def populate_devices(self):
        """
        Заполняет комбобокс списком доступных аудиоустройств вывода.
        Первый элемент — устройство по умолчанию (userData = None).
        """
        self.device_combo.clear()
        self.device_combo.addItem("Устройство по умолчанию", None)
        devices = self.sound_manager.get_output_devices()
        for idx, name in devices:
            self.device_combo.addItem(name, idx)

        # Восстанавливаем текущее устройство
        current_idx = self.sound_manager.current_device
        if current_idx is None:
            self.device_combo.setCurrentIndex(0)
        else:
            for i in range(self.device_combo.count()):
                if self.device_combo.itemData(i) == current_idx:
                    self.device_combo.setCurrentIndex(i)
                    break
            else:
                self.device_combo.setCurrentIndex(0)

    def update_custom_sound_label(self):
        """
        Обновляет подпись с информацией о пользовательском звуке
        для текущего выбранного региона.

        :return: None.
        """
        current_path = self.sound_manager.custom_sounds.get(self.current_region, "").strip()

        if current_path:
            path_obj = Path(current_path)
            self.custom_sound_path_label.setText(f"Пользовательский файл:\n{path_obj.name}")
            self.custom_sound_path_label.setToolTip(current_path)
            self.reset_sound_btn.setEnabled(True)
        else:
            builtin_name = self.sound_manager.get_builtin_sound_filename()
            self.custom_sound_path_label.setText(f"Стандартный встроенный звук:\n{builtin_name}")
            self.custom_sound_path_label.setToolTip("")
            self.reset_sound_btn.setEnabled(False)

    def choose_custom_sound(self):
        """
        Открывает диалог выбора пользовательского аудиофайла
        для текущего региона и применяет его.

        :return: None.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Выбор звука для региона '{self.current_region}'",
            "",
            "Аудиофайлы (*.mp3 *.wav);;MP3 (*.mp3);;WAV (*.wav)",
        )

        if not file_path:
            return

        self.sound_manager.set_custom_sound(self.current_region, file_path)
        self.update_custom_sound_label()

    def reset_custom_sound(self):
        """
        Сбрасывает пользовательский звук текущего региона
        и возвращает встроенный стандартный файл.

        :return: None.
        """
        self.sound_manager.clear_custom_sound(self.current_region)
        self.update_custom_sound_label()

    def cleanup_unused_custom_sound_files(self):
        """
        Удаляет старые пользовательские файлы после подтверждения изменений,
        если они больше не используются в текущих настройках.

        :return: None.
        """
        current_paths = {
            Path(path).resolve() for path in self.sound_manager.custom_sounds.values() if path and Path(path).exists()
        }

        user_sounds_dir = self.sound_manager.get_user_sounds_dir().resolve()

        for old_path in self.original_custom_sounds.values():
            if not old_path:
                continue

            old_file = Path(old_path)
            try:
                resolved_old_file = old_file.resolve()
            except Exception:
                continue

            if resolved_old_file in current_paths:
                continue

            if not old_file.exists() or not old_file.is_file():
                continue

            if user_sounds_dir not in resolved_old_file.parents:
                continue

            try:
                old_file.unlink()
                logger.info(f"Удалён неиспользуемый пользовательский звук: {old_file}")
            except Exception as e:
                logger.error(
                    f"Ошибка при удалении неиспользуемого пользовательского звука '{old_file}': {e}",
                    exc_info=True,
                )

    def on_volume_changed(self, value):
        """Обрабатывает изменение громкости слайдером."""
        self.volume_label.setText(f"{value}%")
        self.sound_manager.set_volume(value / 100.0)
        self.update_volume_icon(value)

    def on_device_changed(self, index):
        """
        Обрабатывает выбор устройства в комбобоксе.
        При неудачном переключении восстанавливает предыдущее устройство.
        """
        if not self.device_combo.isEnabled():
            return
        device_index = self.device_combo.currentData()
        success = self.sound_manager.set_device_by_index(device_index)
        if not success:
            # Возвращаем комбобокс к предыдущему значению
            current_idx = self.sound_manager.current_device
            self.device_combo.blockSignals(True)
            if current_idx is None:
                self.device_combo.setCurrentIndex(0)
            else:
                for i in range(self.device_combo.count()):
                    if self.device_combo.itemData(i) == current_idx:
                        self.device_combo.setCurrentIndex(i)
                        break
                else:
                    self.device_combo.setCurrentIndex(0)
            self.device_combo.blockSignals(False)

    def test_sound(self):
        """Воспроизводит тестовый звук через текущее устройство."""
        self.sound_manager.test_sound()

    def accept(self):
        """
        Подтверждает изменения, удаляет старые неиспользуемые
        пользовательские звуки и закрывает диалог.

        :return: None.
        """
        self.cleanup_unused_custom_sound_files()
        self._accepted = True
        super().accept()

    def rollback_changes(self):
        """
        Возвращает исходные громкость, устройство вывода
        и пользовательские звуки по регионам.

        :return: None.
        """
        self.sound_manager.set_volume(self.original_volume)
        self.sound_manager.set_device_by_index(self.original_device)
        self.sound_manager.custom_sounds = dict(self.original_custom_sounds)
        self.sound_manager.load_alarm_sound()
        self.update_custom_sound_label()

    def reject(self):
        """
        Отменяет изменения и закрывает диалог с откатом
        всех временно применённых параметров.

        :return: None.
        """
        self.rollback_changes()
        super().reject()

    def closeEvent(self, event):
        """
        При закрытии окна без подтверждения откатывает
        все временные изменения.

        :param event: Событие закрытия окна.
        :return: None.
        """
        if not self._accepted:
            self.rollback_changes()
        super().closeEvent(event)
