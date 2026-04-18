import time

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QPalette
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QPushButton, QScrollArea, QSizePolicy, QSpinBox, QStyle, QVBoxLayout,
                             QWidget)

from src.gui.area_selector import AreaSelector
from src.gui.widgets import NotificationWidget, RoundedGroupBox, StyledButton, TitleBar
from src.monitor.screen_monitor import ScreenMonitorThread
from src.utils.logger_config import setup_logger
from src.utils.settings import load_env_settings, save_settings
from src.utils.sound_manager import sound_manager
from src.utils.telegram import send_telegram_message

logger = setup_logger("app.log", __name__)


class MainWindow(QMainWindow):
    """
    Главное окно приложения Screen Monitor.
    Содержит все элементы управления: настройки мониторинга, область логов,
    кнопки запуска/остановки, выбор региона и т.д.
    """

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

    def __init__(self):
        logger.info("Инициализация главного окна приложения")
        super().__init__()

        try:
            self.setWindowTitle("Screen Monitor")

            # Масштабирование окна под текущий DPI экрана
            screen = QApplication.primaryScreen()
            dpi_scale = screen.logicalDotsPerInch() / 96.0
            base_width = int(520 * dpi_scale)
            base_height = int(650 * dpi_scale)
            self.resize(base_width, base_height)
            # Центрируем окно на экране
            self.move(screen.availableGeometry().center() - self.rect().center())

            # Иконка окна (если файл существует)
            icon_path = self.get_resource_path("icons/app_icon.png")
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))

            # Убираем стандартную рамку и делаем фон прозрачным (для скруглённых углов)
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground, True)

            # Таймер для обновления индикатора времени до следующей проверки
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_timer_display)
            self.next_check_time = 0

            # Переменные для состояния
            self.telegram_enabled = False

            # Загружаем настройки из .env файла
            self.env_path = ".env"
            logger.debug(f"Загрузка настроек из файла: {self.env_path}")
            self.current_settings = load_env_settings(self.env_path)

            # Загружаем пользовательские звуки из настроек
            sound_manager.load_custom_sounds_from_settings(self.current_settings)

            # Инициализация звукового менеджера с сохранёнными параметрами
            current_region = self.current_settings.get("REGION", "Волга")
            sound_manager.set_region(current_region)

            volume_str = self.current_settings.get("SOUND_VOLUME", "50")
            try:
                volume = int(volume_str) / 100.0
                sound_manager.set_volume(volume)
            except:
                sound_manager.set_volume(0.5)

            saved_device = self.current_settings.get("AUDIO_DEVICE", "")
            if saved_device:
                try:
                    idx = int(saved_device)
                    sound_manager.set_device_by_index(idx)
                except ValueError:
                    sound_manager.set_device_by_index(None)
            else:
                sound_manager.set_device_by_index(None)

            # Построение интерфейса
            self.init_ui()
            logger.info("Главное окно успешно инициализировано")

        except Exception as e:
            logger.critical(f"Ошибка при инициализации главного окна: {str(e)}", exc_info=True)
            raise

    def init_ui(self):
        """
        Создаёт все визуальные элементы главного окна: заголовок, группы настроек,
        панель управления, журнал событий.
        """
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

        # Внешний контейнер с тонкой рамкой (имитация границы)
        outer_widget = QWidget()
        outer_layout = QVBoxLayout(outer_widget)
        outer_layout.setContentsMargins(1, 1, 1, 1)
        outer_layout.setSpacing(0)

        # Внутренний контейнер (основной фон)
        self.central_widget = QWidget()
        self.central_widget.setObjectName("mainContainer")

        outer_layout.addWidget(self.central_widget)
        self.setCentralWidget(outer_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(0)

        # Кастомный заголовок окна (с кнопками свернуть/закрыть)
        self.title_bar = TitleBar(self)
        self.main_layout.addWidget(self.title_bar)

        # Область основного контента
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 10, 20, 15)
        content_layout.setSpacing(20)

        # Заголовок приложения
        title_label = QLabel("Screen Monitor")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setStyleSheet("color: #f8faff; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)

        # Область мониторинга из настроек (по умолчанию)
        monitor_area = {
            "left": int(self.current_settings.get("MONITOR_LEFT", 11)),
            "top": int(self.current_settings.get("MONITOR_TOP", 233)),
            "width": int(self.current_settings.get("MONITOR_WIDTH", 1976)),
            "height": int(self.current_settings.get("MONITOR_HEIGHT", 220)),
        }

        # Поток мониторинга
        self.monitor_thread = ScreenMonitorThread(monitor_area=monitor_area)
        self.monitor_thread.change_detected.connect(self.update_log)
        self.monitor_thread.status_update.connect(self.update_status)
        self.monitor_thread.check_completed.connect(self.on_check_completed)
        logger.debug("Поток мониторинга инициализирован")

        # Группы настроек и элементов управления
        self.create_settings_group(content_layout)
        self.create_controls(content_layout)
        self.create_log_group(content_layout)

        self.main_layout.addWidget(content_widget)

        # Глобальные стили для виджетов
        self.setStyleSheet(
            """
            #mainContainer {
                background-color: #292a2d;
                border: 1px solid #4d6bfe;
                border-radius: 12px;
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

            QLineEdit {
                background-color: #3a3c42;
                color: #f8faff;
                border: 1px solid #4d6bfe;
                border-radius: 6px;
                padding: 5px;
            }
        """
        )

    def create_settings_group(self, layout):
        """
        Формирует группу настроек мониторинга:
        - выбор региона
        - интервал проверки
        - настройки Telegram
        - настройки Windows-уведомлений
        - кнопка сохранения
        """
        logger.debug("Создание группы настроек")
        try:
            settings_group = RoundedGroupBox("Настройки мониторинга")
            settings_layout = QVBoxLayout()
            settings_layout.setSpacing(12)

            # Регион и кнопка настроек звука
            region_row = QHBoxLayout()
            region_row.addWidget(QLabel("Регион:"))
            self.region_combo = QComboBox()
            self.region_combo.addItems(
                [
                    "Волга",
                    "Юг",
                    "Северо-Запад",
                    "Центр",
                    "Москва",
                    "Дальний Восток",
                    "Сибирь",
                    "Урал",
                ]
            )
            current_region = self.current_settings.get("REGION", "Волга")
            self.region_combo.setCurrentText(current_region)
            self.region_combo.currentTextChanged.connect(self.on_region_changed)
            region_row.addWidget(self.region_combo)

            # Кнопка открытия диалога настроек звука
            self.sound_settings_btn = QPushButton("⚙ Настройки звука")
            self.sound_settings_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            self.sound_settings_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #3a3c42;
                    color: #f8faff;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4d6bfe;
                }
            """
            )
            self.sound_settings_btn.clicked.connect(self.open_sound_settings)
            region_row.addWidget(self.sound_settings_btn)
            region_row.addStretch()
            settings_layout.addLayout(region_row)

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

            # Настройки Telegram
            telegram_group = RoundedGroupBox("Настройки Telegram")
            telegram_layout = QVBoxLayout()
            telegram_layout.setSpacing(10)

            self.telegram_checkbox = QCheckBox("Включить Telegram-уведомления")
            self.telegram_checkbox.setStyleSheet("color: #f8faff;")
            self.telegram_checkbox.setChecked(self.current_settings.get("TELEGRAM_ENABLED", "False").lower() == "true")
            self.telegram_checkbox.stateChanged.connect(self.toggle_telegram_notifications)
            telegram_layout.addWidget(self.telegram_checkbox)

            # Поле ввода ID и кнопка теста
            chat_layout = QHBoxLayout()
            chat_layout.setSpacing(8)
            chat_layout.addWidget(QLabel("Ваш Telegram ID:"))

            self.telegram_chat_input = QLineEdit()
            self.telegram_chat_input.setPlaceholderText("Вставьте ваш ID из бота")
            self.telegram_chat_input.setText(self.current_settings.get("TELEGRAM_CHAT_ID", ""))
            self.telegram_chat_input.setMinimumWidth(180)
            self.telegram_chat_input.setStyleSheet(
                """
                QLineEdit {
                    background-color: #3a3c42;
                    color: #f8faff;
                    border: 1px solid #4d6bfe;
                    border-radius: 6px;
                    padding: 5px;
                }
            """
            )
            chat_layout.addWidget(self.telegram_chat_input)

            self.test_telegram_btn = QPushButton("Тест Telegram")
            self.test_telegram_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            self.test_telegram_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #3a3c42;
                    color: #f8faff;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4d6bfe;
                }
            """
            )
            self.test_telegram_btn.clicked.connect(self.test_telegram)
            chat_layout.addWidget(self.test_telegram_btn)
            chat_layout.addStretch()
            telegram_layout.addLayout(chat_layout)

            # Подсказка о боте
            bot_info = QLabel(
                "Получить Telegram ID можно в боте: "
                "<a style='color: #0088cc;' href='https://t.me/monitoringbti_bot'>@monitoringbti_bot</a>"
            )
            bot_info.setOpenExternalLinks(True)
            bot_info.setWordWrap(True)
            bot_info.setStyleSheet(
                """
                QLabel {
                    color: #b5b7be;
                    margin-top: 6px;
                }
                QLabel a {
                    color: #7aa2f7;
                    text-decoration: none;
                }
                QLabel a:hover {
                    text-decoration: underline;
                }
            """
            )
            telegram_layout.addWidget(bot_info)

            telegram_group.setLayout(telegram_layout)
            settings_layout.addWidget(telegram_group)

            # Настройки Windows-уведомлений
            windows_group = RoundedGroupBox("Настройки Windows-уведомлений")
            windows_layout = QVBoxLayout()
            windows_layout.setSpacing(10)

            self.windows_checkbox = QCheckBox("Включить всплывающие уведомления")
            self.windows_checkbox.setStyleSheet("color: #f8faff;")
            self.windows_checkbox.setChecked(
                self.current_settings.get("WINDOWS_NOTIFICATIONS_ENABLED", "True").lower() == "true"
            )
            self.windows_checkbox.stateChanged.connect(self.toggle_windows_notifications)
            windows_layout.addWidget(self.windows_checkbox)

            notify_layout = QHBoxLayout()
            notify_layout.addWidget(QLabel("Длительность показа:"))
            self.notify_duration_spin = QSpinBox()
            self.notify_duration_spin.setRange(5, 60)
            self.notify_duration_spin.setValue(15)
            self.notify_duration_spin.setSuffix(" сек")
            notify_layout.addWidget(self.notify_duration_spin)
            notify_layout.addStretch()
            windows_layout.addLayout(notify_layout)

            windows_group.setLayout(windows_layout)
            settings_layout.addWidget(windows_group)

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
        """
        Создаёт панель управления: кнопки запуска/остановки, выбора области,
        индикатор времени до следующей проверки и статусную строку.
        """
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

            self.area_btn = StyledButton("Выбрать область")
            self.area_btn.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
            self.area_btn.clicked.connect(self.select_monitor_area)
            controls_layout.addWidget(self.area_btn)

            # Таймер обратного отсчёта
            self.timer_label = QLabel("До проверки: ---")
            self.timer_label.setFont(QFont("Segoe UI", 10))
            self.timer_label.setStyleSheet("color: #4d6bfe; font-weight: bold;")
            controls_layout.addWidget(self.timer_label)

            layout.addLayout(controls_layout)

            # Статусная строка
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

            self.area_info = QLabel(
                f"Область: {self.monitor_thread.monitor['width']}x{self.monitor_thread.monitor['height']}"
            )
            self.area_info.setObjectName("areaInfo")
            self.area_info.setFont(QFont("Segoe UI", 9))
            self.area_info.setStyleSheet("color: #7d7f86;")
            status_layout.addWidget(self.area_info)

            # Кнопка предпросмотра области (глаз)
            self.preview_btn = QPushButton("👁")
            self.preview_btn.setMinimumSize(32, 32)
            self.preview_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.preview_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #3a3c42;
                    color: #f8faff;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #4d6bfe;
                }
            """
            )
            self.preview_btn.setToolTip("Предпросмотр выбранной области")
            self.preview_btn.clicked.connect(self.preview_selected_area)
            status_layout.addWidget(self.preview_btn)

            layout.addWidget(self.status_frame)

        except Exception as e:
            logger.error(f"Ошибка при создании элементов управления: {str(e)}", exc_info=True)
            raise

    def on_region_changed(self, region):
        """
        Обработчик смены региона в комбобоксе.
        Обновляет настройки, звуковой менеджер и сохраняет изменения.
        """
        logger.info(f"Выбран регион: {region}")
        self.current_settings["REGION"] = region
        sound_manager.set_region(region)
        self.save_settings()
        self.update_log(f"Регион изменен на: {region}")

    def update_timer_display(self):
        """
        Обновляет текст таймера, показывая время до следующей проверки.
        Меняет цвет в зависимости от оставшегося времени.
        """
        if self.monitor_thread.isRunning():
            current_time = time.time()
            remaining = max(0, self.next_check_time - current_time)

            if remaining < 1:
                remaining_str = f"{remaining:.1f}"
            else:
                remaining_str = f"{int(remaining)}"

            self.timer_label.setText(f"До проверки: {remaining_str}с")

            if remaining < 0.5 and remaining >= 0:
                self.timer_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
            elif remaining < 3:
                self.timer_label.setStyleSheet("color: #ffa726; font-weight: bold;")
            else:
                self.timer_label.setStyleSheet("color: #4d6bfe; font-weight: bold;")
        else:
            self.timer_label.setText("До проверки: ---")
            self.timer_label.setStyleSheet("color: #4d6bfe; font-weight: bold;")

    def create_log_group(self, layout):
        """
        Создаёт группу с прокручиваемым журналом событий.
        В журнал будут добавляться сообщения о старте/остановке, обнаружении аварий и т.д.
        """
        logger.debug("Создание группы журнала событий")
        try:
            log_group = RoundedGroupBox("Журнал событий")
            log_layout = QVBoxLayout()

            # Задаём минимальную высоту, чтобы журнал был заметен
            log_group.setMinimumHeight(160)

            # Область прокрутки
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scroll_area.setMinimumHeight(120)

            # Контейнер для записей
            self.log_container = QWidget()
            self.log_container.setStyleSheet("background-color: #212327; border-radius: 8px;")
            self.log_layout = QVBoxLayout(self.log_container)
            self.log_layout.setContentsMargins(15, 15, 15, 15)
            self.log_layout.setSpacing(8)

            # Заглушка, пока нет событий
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
        """
        Обрабатывает изменение состояния чекбокса Telegram-уведомлений.
        Обновляет внутренний флаг и добавляет запись в журнал.
        """
        self.telegram_enabled = state == Qt.Checked
        status = "включены" if self.telegram_enabled else "отключены"
        logger.info(f"Telegram уведомления {status}")
        self.update_log(f"Telegram уведомления {status}")

    def toggle_windows_notifications(self, state):
        """
        Обрабатывает изменение состояния чекбокса всплывающих уведомлений Windows.
        """
        enabled = state == Qt.Checked
        status = "включены" if enabled else "отключены"
        logger.info(f"Windows уведомления {status}")
        self.update_log(f"Windows уведомления {status}")

    def save_settings(self):
        """
        Сохраняет текущие значения всех настроек в .env файл.
        Использует функцию save_settings из utils.settings. Если изменения были,
        выводит сообщение в журнал.

        :return: None.
        """
        logger.debug("Попытка сохранения настроек")
        try:
            new_settings = {
                "INTERVAL": str(self.interval_spin.value()),
                "TELEGRAM_ENABLED": str(self.telegram_checkbox.isChecked()),
                "TELEGRAM_CHAT_ID": self.telegram_chat_input.text(),
                "WINDOWS_NOTIFICATIONS_ENABLED": str(self.windows_checkbox.isChecked()),
                "MONITOR_LEFT": str(self.monitor_thread.monitor["left"]),
                "MONITOR_TOP": str(self.monitor_thread.monitor["top"]),
                "MONITOR_WIDTH": str(self.monitor_thread.monitor["width"]),
                "MONITOR_HEIGHT": str(self.monitor_thread.monitor["height"]),
                "REGION": self.region_combo.currentText(),
                "SOUND_VOLUME": str(int(sound_manager.get_volume() * 100)),
                "AUDIO_DEVICE": "" if sound_manager.current_device is None else str(sound_manager.current_device),
                "CUSTOM_SOUND_VOLGA": sound_manager.custom_sounds.get("Волга", ""),
                "CUSTOM_SOUND_SOUTH": sound_manager.custom_sounds.get("Юг", ""),
                "CUSTOM_SOUND_NORTHWEST": sound_manager.custom_sounds.get("Северо-Запад", ""),
                "CUSTOM_SOUND_CENTER": sound_manager.custom_sounds.get("Центр", ""),
                "CUSTOM_SOUND_MIMO": sound_manager.custom_sounds.get("Москва", ""),
                "CUSTOM_SOUND_EAST": sound_manager.custom_sounds.get("Дальний Восток", ""),
                "CUSTOM_SOUND_SIBERIA": sound_manager.custom_sounds.get("Сибирь", ""),
                "CUSTOM_SOUND_URAL": sound_manager.custom_sounds.get("Урал", ""),
            }

            if save_settings(self.env_path, new_settings):
                self.current_settings.update(new_settings)
                logger.info("Настройки успешно сохранены")
                self.update_log("Настройки сохранены")
            else:
                logger.debug("Изменений в настройках не обнаружено")

        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек: {str(e)}", exc_info=True)
            self.update_log("⛔ Ошибка при сохранении настроек")

    def show_incident_notification(self, message):
        """
        Отображает всплывающее уведомление об обнаруженной аварии.
        Уведомление показывается только если включены Windows-уведомления.
        """
        if not self.windows_checkbox.isChecked():
            logger.debug("Windows-уведомления отключены, пропускаем показ")
            return

        logger.debug(f"show_incident_notification: {message[:50]}...")

        # Убираем из сообщения информацию о площади (всё после первой открывающей скобки)
        clean_message = message.split("(")[0].strip()
        duration = self.notify_duration_spin.value()

        notification = NotificationWidget(clean_message, self, duration=duration, title="Обнаружена авария")

        # Позиционируем в правом нижнем углу экрана
        screen_geo = QApplication.primaryScreen().availableGeometry()
        notification.move(
            screen_geo.width() - notification.width() - 20, screen_geo.height() - notification.height() - 20
        )
        notification.show()
        notification.raise_()
        notification.activateWindow()
        logger.debug("Уведомление об аварии показано")

    def test_telegram(self):
        """
        Отправляет тестовое сообщение в Telegram, чтобы проверить правильность введённого ID
        и работоспособность бота. Результат отображается в журнале.
        """
        logger.debug("Тестирование соединения с Telegram")
        try:
            if not self.telegram_checkbox.isChecked():
                logger.warning("Попытка тестирования Telegram при отключенных уведомлениях")
                self.update_log("⚠️ Включите Telegram-уведомления для тестирования!")
                return

            chat_id = self.telegram_chat_input.text().strip()
            if not chat_id:
                logger.warning("Попытка тестирования Telegram без указания ID")
                self.update_log("⚠️ Получите и введите ваш ID из бота @monitoringbti_bot!")
                return

            logger.info(f"Отправка тестового сообщения в Telegram (chat_id: {chat_id})")
            test_message = "🟢 Тестовое уведомление от Screen Monitor"
            result = send_telegram_message(chat_id, test_message)
            logger.info(f"Результат теста Telegram: {result}")
            self.update_log(result)

        except Exception as e:
            logger.error(f"Ошибка при тестировании Telegram: {str(e)}", exc_info=True)
            self.update_log("⚠️ Ошибка при тестировании Telegram")

    def select_monitor_area(self):
        """
        Открывает диалог AreaSelector для интерактивного выбора области мониторинга.
        После подтверждения обновляет настройки и перезапускает мониторинг с новой областью.
        """
        logger.info("Запуск выбора области мониторинга")

        # Текущая область из настроек
        current_area = {
            "left": int(self.current_settings.get("MONITOR_LEFT", 11)),
            "top": int(self.current_settings.get("MONITOR_TOP", 233)),
            "width": int(self.current_settings.get("MONITOR_WIDTH", 1976)),
            "height": int(self.current_settings.get("MONITOR_HEIGHT", 220)),
        }

        selector = AreaSelector(self, current_area)
        if selector.exec_() == QDialog.Accepted:
            selected_area = selector.get_selected_area()

            logger.info(f"Выбрана область: {selected_area}")

            # Обновляем настройки
            self.current_settings.update(
                {
                    "MONITOR_LEFT": str(selected_area["left"]),
                    "MONITOR_TOP": str(selected_area["top"]),
                    "MONITOR_WIDTH": str(selected_area["width"]),
                    "MONITOR_HEIGHT": str(selected_area["height"]),
                }
            )

            # Меняем область в работающем потоке (поток подхватит новое значение при следующем захвате)
            self.monitor_thread.monitor = selected_area

            logger.info(f"Область мониторинга обновлена: {selected_area}")
            self.update_log(f"Область мониторинга обновлена: {selected_area['width']}x{selected_area['height']}")

            self.update_area_info()
            self.save_settings()

    def preview_selected_area(self):
        """
        Показывает модальное окно с предпросмотром текущей выбранной области.
        Захватывает скриншот этой области и отображает его вместе с информацией о координатах.
        Используется для визуальной проверки корректности выбора.
        """
        try:
            from mss import mss
            from PIL import Image
            from PIL.ImageQt import ImageQt
            from PyQt5.QtCore import Qt
            from PyQt5.QtGui import QIcon, QPixmap
            from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout

            from src.gui.widgets import StyledButton
            from src.utils.screen_utils import get_physical_area

            monitor_area = self.monitor_thread.monitor
            # Получаем физические координаты для захвата
            physical_area = get_physical_area(monitor_area)

            with mss() as sct:
                monitors = sct.monitors[1:]
                # Определяем, какому монитору принадлежит скорректированная область
                target_monitor = None
                for monitor in monitors:
                    if (
                        physical_area["left"] >= monitor["left"]
                        and physical_area["top"] >= monitor["top"]
                        and physical_area["left"] + physical_area["width"] <= monitor["left"] + monitor["width"]
                        and physical_area["top"] + physical_area["height"] <= monitor["top"] + monitor["height"]
                    ):
                        target_monitor = monitor
                        break
                if not target_monitor:
                    target_monitor = monitors[0]

                screenshot = sct.grab(physical_area)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

            # Преобразуем PIL Image в QPixmap
            qimage = ImageQt(img).copy()
            pixmap = QPixmap.fromImage(qimage)

            # Получаем масштаб экрана и логические размеры области
            logical_width = monitor_area["width"]
            logical_height = monitor_area["height"]

            # Создаём диалог предпросмотра
            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle("Предпросмотр области мониторинга")

            # Иконка окна
            icon_path = self.get_resource_path("icons/app_icon.png")
            if icon_path.exists():
                preview_dialog.setWindowIcon(QIcon(str(icon_path)))

            preview_dialog.setStyleSheet(
                """
                QDialog {
                    background-color: #292a2d;
                    color: #f8faff;
                }
            """
            )

            preview_dialog.setWindowFlags(preview_dialog.windowFlags() | Qt.WindowMinimizeButtonHint)

            # Размер окна подстраиваем под логический размер изображения + отступы
            window_width = logical_width + 40
            window_height = logical_height + 200
            preview_dialog.setFixedSize(window_width, window_height)

            layout = QVBoxLayout(preview_dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)

            # Изображение – фиксированный логический размер с масштабированием
            image_label = QLabel()
            image_label.setFixedSize(logical_width, logical_height)
            image_label.setPixmap(pixmap)
            image_label.setScaledContents(True)  # масштабируем под размер label'а
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setStyleSheet("border: 2px solid #4d6bfe; border-radius: 8px;")
            layout.addWidget(image_label)

            # Информация о координатах
            info_label = QLabel(
                f"<b>Выбранная область:</b> {monitor_area['width']}x{monitor_area['height']} "
                f"({monitor_area['left']}, {monitor_area['top']})<br>"
                f"<b>С учётом смещения:</b> {physical_area['left']}, {physical_area['top']}<br>"
                f"<b>Монитор:</b> {target_monitor['width']}x{target_monitor['height']} "
                f"({target_monitor['left']}, {target_monitor['top']})"
            )
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet(
                """
                color: #f8faff; 
                background-color: #3a3c42; 
                padding: 12px; 
                border-radius: 8px;
                font-size: 13px;
                font-family: 'Segoe UI';
            """
            )
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

            close_btn = StyledButton("Закрыть")
            close_btn.clicked.connect(preview_dialog.accept)
            layout.addWidget(close_btn)

            # Центрируем окно на экране
            screen_geo = QApplication.primaryScreen().availableGeometry()
            x = (screen_geo.width() - preview_dialog.width()) // 2
            y = (screen_geo.height() - preview_dialog.height()) // 2
            preview_dialog.move(x, y)

            preview_dialog.exec_()

        except Exception as e:
            logger.error(f"Ошибка при предпросмотре области: {str(e)}")
            self.update_log("⛔️ Ошибка при предпросмотре области")

    def update_area_info(self):
        """Обновляет информацию о выбранной области в интерфейсе."""
        try:
            monitor = self.monitor_thread.monitor
            self.area_info.setText(
                f"Область: {monitor['width']}x{monitor['height']} ({monitor['left']},{monitor['top']})"
            )
        except Exception as e:
            logger.error(f"Ошибка при обновлении информации об области: {str(e)}")

    def start_monitoring(self):
        """
        Запускает поток мониторинга и активирует соответствующие кнопки.
        Также запускает таймер для отображения времени до следующей проверки.
        """
        logger.info("Запуск мониторинга экрана")
        try:
            self.monitor_thread.check_interval = self.interval_spin.value()
            self.next_check_time = time.time() + self.monitor_thread.check_interval
            self.timer.start(500)  # обновление таймера каждые 0.5 сек
            self.update_timer_display()

            logger.debug(f"Параметры мониторинга: интервал={self.interval_spin.value()}с")

            self.monitor_thread.start()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Статус: Мониторинг активен")
            self.update_log("Мониторинг запущен")
            logger.info("Мониторинг успешно запущен")

        except Exception as e:
            logger.error(f"Ошибка при запуске мониторинга: {str(e)}", exc_info=True)
            self.update_log("⛔ Ошибка при запуске мониторинга")

    def stop_monitoring(self):
        """
        Останавливает поток мониторинга и таймер, обновляет состояние кнопок.
        """
        logger.info("Остановка мониторинга экрана")
        try:
            self.monitor_thread.stop()
            self.timer.stop()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Статус: Остановлено")
            self.update_log("Мониторинг остановлен")
            logger.info("Мониторинг успешно остановлен")

        except Exception as e:
            logger.error(f"Ошибка при остановке мониторинга: {str(e)}", exc_info=True)
            self.update_log("⛔ Ошибка при остановке мониторинга")

    def on_check_completed(self):
        """
        Слот, вызываемый каждый раз после завершения цикла проверки в потоке.
        Обновляет время следующей проверки.
        """
        self.next_check_time = time.time() + self.monitor_thread.check_interval
        self.update_timer_display()

    def open_sound_settings(self):
        """
        Открывает диалог настройки звука (SoundSettingsDialog).
        После закрытия диалога с подтверждением сохраняет изменения в .env.
        """
        from src.gui.widgets import SoundSettingsDialog

        dialog = SoundSettingsDialog(sound_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.save_settings()
            logger.debug("Настройки звука сохранены")

    def update_log(self, message):
        """
        Добавляет новую запись в журнал событий.
        Если запись содержит индикатор новой аварии, инициирует отправку Telegram-уведомления
        и показывает всплывающее окно.
        """
        try:
            # Удаляем заглушку, если она есть
            if (
                self.log_layout.count() == 1
                and self.log_layout.itemAt(0).widget().text() == "Здесь будут отображаться события мониторинга"
            ):
                self.log_layout.itemAt(0).widget().deleteLater()

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

            # Автопрокрутка вниз
            QTimer.singleShot(
                0,
                lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()),
            )

            # Если это сообщение о новой аварии
            if "🔴 Обнаружена новая авария" in message:
                # Показываем всплывающее уведомление (если включены Windows-уведомления)
                self.show_incident_notification(message)

                # Отправляем Telegram, если включено
                if self.telegram_checkbox.isChecked():
                    chat_id = self.telegram_chat_input.text().strip()
                    if chat_id:
                        logger.debug(f"Отправка сообщения в Telegram: {message}")
                        result = send_telegram_message(chat_id, message)
                        logger.debug(f"Результат отправки: {result}")
                        # Уведомление об отправке больше не показываем (можно убрать или оставить отдельно)
                        # если хотите оставить уведомление об отправке, создайте другой метод с другим заголовком
                    else:
                        logger.debug("Не указан chat_id для Telegram")
                else:
                    logger.debug("Telegram-уведомления отключены, пропускаем отправку")

        except Exception as e:
            logger.error(f"Ошибка при обновлении журнала: {str(e)}", exc_info=True)

    def update_status(self, message):
        """
        Обновляет текст статусной строки внизу окна. Используется для отображения текущего состояния мониторинга.
        """
        try:
            self.status_label.setText(f"Статус: {message}")
            logger.debug(f"Обновление статуса: {message}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса: {str(e)}", exc_info=True)

    def closeEvent(self, event):
        """
        Переопределённый обработчик закрытия окна.
        Сохраняет настройки и останавливает поток мониторинга, если он активен.
        """
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
        """
        Запоминает позицию курсора относительно окна для последующего перетаскивания.
        """
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """
        Перемещает главное окно при зажатой левой кнопке мыши.
        """
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
