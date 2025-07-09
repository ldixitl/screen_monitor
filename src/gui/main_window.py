import time
from collections import deque

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import (QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QScrollArea, QSpinBox,
                             QVBoxLayout, QWidget, QStyle)

from src.monitor.screen_monitor import ScreenMonitorThread
from src.utils.logger_config import setup_logger
from src.utils.settings import load_env_settings, save_settings
from src.utils.telegram import send_telegram_message, test_telegram_connection
from src.gui.widgets import RoundedGroupBox, StyledButton, TitleBar

logger = setup_logger("app.log", __name__)


class MainWindow(QMainWindow):
    def __init__(self):
        logger.info("Инициализация главного окна приложения")
        super().__init__()

        try:
            self.setWindowTitle("Screen Monitor")
            self.setGeometry(100, 100, 500, 600)
            self.setStyleSheet(
                """
                QMainWindow {
                    background-color: #292a2d;
                    border: 3px solid #4d6bfe;
                    border-radius: 12px;
                }
            """
            )
            self.setWindowFlags(Qt.FramelessWindowHint)

            # Настройки
            self.telegram_queue = deque(maxlen=10)
            self.telegram_enabled = False
            self.env_path = "../../.env"
            logger.debug(f"Загрузка настроек из файла: {self.env_path}")
            self.current_settings = load_env_settings(self.env_path)

            # Инициализация UI
            self.init_ui()
            logger.info("Главное окно успешно инициализировано")

        except Exception as e:
            logger.critical(f"Ошибка при инициализации главного окна: {str(e)}", exc_info=True)
            raise

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        logger.debug("Настройка цветовой палитры")
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#292a2d"))
        palette.setColor(QPalette.WindowText, QColor("#f8faff"))
        palette.setColor(QPalette.Base, QColor("#212327"))
        palette.setColor(QPalette.AlternateBase, QColor("#3a3c42"))
        palette.setColor(QPalette.Text, QColor("#f8faff"))
        palette.setColor(QPalette.Button, QColor("#4d6bfe"))
        palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
        palette.setColor(QPalette.Highlight, QColor("#4d6bfe"))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        self.setPalette(palette)

        # Центральный виджет
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralWidget")
        self.setCentralWidget(self.central_widget)

        # Основной лейаут
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(0)

        # Панель заголовка
        self.title_bar = TitleBar(self)
        self.main_layout.addWidget(self.title_bar)

        # Основной контент
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 10, 20, 15)
        content_layout.setSpacing(20)

        # Заголовок
        title_label = QLabel("Screen Monitor")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setStyleSheet("color: #f8faff; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)

        # Виджеты
        self.create_settings_group(content_layout)
        self.create_controls(content_layout)
        self.create_log_group(content_layout)

        self.main_layout.addWidget(content_widget)

        # Стили
        self.setStyleSheet(
            """
            #centralWidget {
                background-color: #292a2d;
            }
            QLabel {
                color: #f8faff;
                font-family: 'Segoe UI';
            }
            QSpinBox {
                background-color: #3a3c42;
                color: #f8faff;
                border: 1px solid #4d6bfe;
                border-radius: 6px;
                padding: 5px;
                min-height: 28px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #212327;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #4d6bfe;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QLineEdit {
                background-color: #3a3c42;
                color: #f8faff;
                border: 1px solid #4d6bfe;
                border-radius: 6px;
                padding: 5px;
                min-height: 28px;
            }
        """
        )

        # Поток мониторинга
        self.monitor_thread = ScreenMonitorThread()
        self.monitor_thread.change_detected.connect(self.update_log)
        self.monitor_thread.status_update.connect(self.update_status)
        logger.debug("Поток мониторинга инициализирован")

    def create_settings_group(self, layout):
        """Создание группы настроек"""
        logger.debug("Создание группы настроек")
        try:
            settings_group = RoundedGroupBox("Настройки мониторинга")
            settings_layout = QVBoxLayout()
            settings_layout.setSpacing(12)

            # Интервал проверки
            interval_layout = QHBoxLayout()
            interval_layout.addWidget(QLabel("Интервал проверки:"))
            self.interval_spin = QSpinBox()
            self.interval_spin.setRange(1, 60)
            self.interval_spin.setValue(int(self.current_settings.get("INTERVAL", 5)))
            self.interval_spin.setSuffix(" сек")
            interval_layout.addWidget(self.interval_spin)
            interval_layout.addStretch()
            settings_layout.addLayout(interval_layout)

            # Порог изменений
            threshold_layout = QHBoxLayout()
            threshold_layout.addWidget(QLabel("Порог изменений:"))
            self.threshold_spin = QSpinBox()
            self.threshold_spin.setRange(1, 100)
            self.threshold_spin.setValue(int(self.current_settings.get("THRESHOLD", 5)))
            self.threshold_spin.setSuffix("%")
            threshold_layout.addWidget(self.threshold_spin)
            threshold_layout.addStretch()
            settings_layout.addLayout(threshold_layout)

            # Порог пустого экрана
            empty_layout = QHBoxLayout()
            empty_layout.addWidget(QLabel("Порог пустого экрана:"))
            self.empty_threshold_spin = QSpinBox()
            self.empty_threshold_spin.setRange(90, 100)
            self.empty_threshold_spin.setValue(int(self.current_settings.get("EMPTY_THRESHOLD", 99)))
            self.empty_threshold_spin.setSuffix("%")
            empty_layout.addWidget(self.empty_threshold_spin)
            empty_layout.addStretch()
            settings_layout.addLayout(empty_layout)

            # Настройки Telegram
            telegram_group = RoundedGroupBox("Настройки Telegram")
            telegram_layout = QVBoxLayout()

            self.telegram_checkbox = QCheckBox("Включить Telegram-уведомления")
            self.telegram_checkbox.setStyleSheet("color: #f8faff;")
            self.telegram_checkbox.setChecked(self.current_settings.get("TELEGRAM_ENABLED", "False").lower() == "true")
            self.telegram_checkbox.stateChanged.connect(self.toggle_telegram_notifications)
            telegram_layout.addWidget(self.telegram_checkbox)

            token_layout = QHBoxLayout()
            token_layout.addWidget(QLabel("Token бота:"))
            self.telegram_token_input = QLineEdit()
            self.telegram_token_input.setPlaceholderText("Введите токен бота")
            self.telegram_token_input.setText(self.current_settings.get("TELEGRAM_TOKEN", ""))
            token_layout.addWidget(self.telegram_token_input)
            telegram_layout.addLayout(token_layout)

            chat_layout = QHBoxLayout()
            chat_layout.addWidget(QLabel("Chat ID:"))
            self.telegram_chat_input = QLineEdit()
            self.telegram_chat_input.setPlaceholderText("Введите chat_id")
            self.telegram_chat_input.setText(self.current_settings.get("TELEGRAM_CHAT_ID", ""))
            chat_layout.addWidget(self.telegram_chat_input)
            telegram_layout.addLayout(chat_layout)

            telegram_group.setLayout(telegram_layout)
            settings_layout.addWidget(telegram_group)

            # Кнопка сохранения
            self.save_btn = StyledButton("Сохранить настройки")
            self.save_btn.clicked.connect(self.save_settings)
            settings_layout.addWidget(self.save_btn)

            settings_group.setLayout(settings_layout)
            layout.addWidget(settings_group)

        except Exception as e:
            logger.error(f"Ошибка при создании группы настроек: {str(e)}", exc_info=True)
            raise

    def create_controls(self, layout):
        """Создание элементов управления"""
        logger.debug("Создание элементов управления")
        try:
            controls_layout = QHBoxLayout()
            controls_layout.setSpacing(15)

            self.start_btn = StyledButton("Запустить мониторинг")
            self.start_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.start_btn.clicked.connect(self.start_monitoring)
            controls_layout.addWidget(self.start_btn)

            self.stop_btn = StyledButton("Остановить мониторинг")
            self.stop_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
            self.stop_btn.clicked.connect(self.stop_monitoring)
            self.stop_btn.setEnabled(False)
            controls_layout.addWidget(self.stop_btn)

            self.test_telegram_btn = StyledButton("Тест Telegram")
            self.test_telegram_btn.clicked.connect(self.test_telegram)
            controls_layout.addWidget(self.test_telegram_btn)

            layout.addLayout(controls_layout)

            # Статус
            self.status_frame = QFrame()
            self.status_frame.setObjectName("statusFrame")
            self.status_frame.setStyleSheet(
                """
                #statusFrame {
                    background-color: #212327;
                    border-radius: 8px;
                    padding: 12px;
                }
            """
            )
            status_layout = QHBoxLayout(self.status_frame)

            status_icon = QLabel("⏱")
            status_icon.setFont(QFont("Segoe UI", 14))
            status_layout.addWidget(status_icon)

            self.status_label = QLabel("Статус: Остановлено")
            self.status_label.setFont(QFont("Segoe UI", 10))
            status_layout.addWidget(self.status_label)
            status_layout.addStretch()

            layout.addWidget(self.status_frame)

        except Exception as e:
            logger.error(f"Ошибка при создании элементов управления: {str(e)}", exc_info=True)
            raise

    def create_log_group(self, layout):
        """Создание группы журнала событий"""
        logger.debug("Создание группы журнала событий")
        try:
            log_group = RoundedGroupBox("Журнал событий")
            log_layout = QVBoxLayout()

            # Область журнала
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            self.log_container = QWidget()
            self.log_container.setStyleSheet("background-color: #212327; border-radius: 8px;")
            self.log_layout = QVBoxLayout(self.log_container)
            self.log_layout.setContentsMargins(15, 15, 15, 15)
            self.log_layout.setSpacing(8)

            # Начальное сообщение
            initial_log = QLabel("Здесь будут отображаться события мониторинга")
            initial_log.setStyleSheet("color: #7d7f86; font-style: italic;")
            self.log_layout.addWidget(initial_log)

            self.scroll_area.setWidget(self.log_container)
            log_layout.addWidget(self.scroll_area)

            log_group.setLayout(log_layout)
            layout.addWidget(log_group)

        except Exception as e:
            logger.error(f"Ошибка при создании группы журнала: {str(e)}", exc_info=True)
            raise

    def toggle_telegram_notifications(self, state):
        """Переключение уведомлений Telegram"""
        self.telegram_enabled = state == Qt.Checked
        status = "включены" if self.telegram_enabled else "отключены"
        logger.info(f"Telegram уведомления {status}")
        self.update_log(f"Telegram уведомления {status}")

    def save_settings(self):
        """Сохраняет текущие настройки в .env файл"""
        logger.debug("Попытка сохранения настроек")
        try:
            new_settings = {
                "INTERVAL": str(self.interval_spin.value()),
                "THRESHOLD": str(self.threshold_spin.value()),
                "EMPTY_THRESHOLD": str(self.empty_threshold_spin.value()),
                "TELEGRAM_ENABLED": str(self.telegram_checkbox.isChecked()),
                "TELEGRAM_TOKEN": self.telegram_token_input.text(),
                "TELEGRAM_CHAT_ID": self.telegram_chat_input.text(),
            }

            if save_settings(self.env_path, new_settings):
                self.current_settings = new_settings
                logger.info("Настройки успешно сохранены")
                self.update_log("Настройки сохранены")
            else:
                logger.warning("Настройки не были изменены")

        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек: {str(e)}", exc_info=True)
            self.update_log("⚠️ Ошибка при сохранении настроек")

    def test_telegram(self):
        """Тестирование соединения с Telegram"""
        logger.debug("Тестирование соединения с Telegram")
        try:
            token = self.telegram_token_input.text().strip()
            chat_id = self.telegram_chat_input.text().strip()

            if not token or not chat_id:
                logger.warning("Попытка тестирования Telegram без указания токена или chat_id")
                self.update_log("⚠️ Введите токен и chat_id!")
                return

            logger.info(f"Отправка тестового сообщения в Telegram (chat_id: {chat_id})")
            result = test_telegram_connection(token, chat_id)
            logger.info(f"Результат теста Telegram: {result}")
            self.update_log(result)

        except Exception as e:
            logger.error(f"Ошибка при тестировании Telegram: {str(e)}", exc_info=True)
            self.update_log("⚠️ Ошибка при тестировании Telegram")

    def start_monitoring(self):
        """Запуск мониторинга экрана"""
        logger.info("Запуск мониторинга экрана")
        try:
            self.monitor_thread.check_interval = self.interval_spin.value()
            self.monitor_thread.change_threshold = self.threshold_spin.value()
            self.monitor_thread.empty_threshold = self.empty_threshold_spin.value()

            logger.debug(f"Параметры мониторинга: интервал={self.interval_spin.value()}с, "
                         f"порог изменений={self.threshold_spin.value()}%, "
                         f"порог пустого экрана={self.empty_threshold_spin.value()}%")

            self.monitor_thread.start()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Статус: Мониторинг активен")
            self.update_log("Мониторинг запущен")
            logger.info("Мониторинг успешно запущен")

        except Exception as e:
            logger.error(f"Ошибка при запуске мониторинга: {str(e)}", exc_info=True)
            self.update_log("⚠️ Ошибка при запуске мониторинга")

    def stop_monitoring(self):
        """Остановка мониторинга экрана"""
        logger.info("Остановка мониторинга экрана")
        try:
            self.monitor_thread.stop()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Статус: Остановлено")
            self.update_log("Мониторинг остановлен")
            logger.info("Мониторинг успешно остановлен")

        except Exception as e:
            logger.error(f"Ошибка при остановке мониторинга: {str(e)}", exc_info=True)
            self.update_log("⚠️ Ошибка при остановке мониторинга")

    def update_log(self, message):
        """Обновление журнала событий"""
        try:
            # Удаляем начальное сообщение
            if (self.log_layout.count() == 1 and
                    self.log_layout.itemAt(0).widget().text() == "Здесь будут отображаться события мониторинга"):
                self.log_layout.itemAt(0).widget().deleteLater()

            # Новая запись
            log_entry = QLabel(f"{time.strftime('%H:%M:%S')} - {message}")
            log_entry.setFont(QFont("Segoe UI", 9))
            log_entry.setStyleSheet(
                """
                padding: 6px 10px;
                border-radius: 6px;
                background-color: #292a2d;
                color: #f8faff;
            """
            )
            self.log_layout.addWidget(log_entry)
            self.log_container.adjustSize()

            # Автопрокрутка
            QTimer.singleShot(0, lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            ))

            # Отправка в Telegram для важных событий
            if ("🟢 Появилось содержимое" in message or
                    "❗ Обнаружены изменения" in message or
                    "⚠️" in message):
                token = self.telegram_token_input.text().strip()
                chat_id = self.telegram_chat_input.text().strip()
                if token and chat_id:
                    logger.debug(f"Отправка сообщения в Telegram: {message}")
                    send_telegram_message(token, chat_id, message)

        except Exception as e:
            logger.error(f"Ошибка при обновлении журнала: {str(e)}", exc_info=True)

    def update_status(self, message):
        """Обновление статуса"""
        try:
            self.status_label.setText(f"Статус: {message}")
            logger.debug(f"Обновление статуса: {message}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса: {str(e)}", exc_info=True)

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        logger.info("Закрытие приложения")
        try:
            self.save_settings()
            if self.monitor_thread.isRunning():
                logger.debug("Остановка потока мониторинга перед закрытием")
                self.monitor_thread.stop()
            event.accept()
            logger.info("Приложение успешно закрыто")
        except Exception as e:
            logger.critical(f"Ошибка при закрытии приложения: {str(e)}", exc_info=True)
            event.accept()

    def mousePressEvent(self, event):
        """Обработчик нажатия кнопки мыши"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Обработчик перемещения мыши"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
