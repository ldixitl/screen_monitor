import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def get_resource_path(relative_path: str) -> Path:
    """
    Возвращает абсолютный путь к файлу ресурса.
    Работает как в режиме разработки, так и в скомпилированном EXE (PyInstaller).

    :param relative_path: Относительный путь внутри папки resources (например, "icons/app_icon.png").
    :return: Объект Path с полным путём к ресурсу.
    """
    if getattr(sys, "frozen", False):
        # Для исполняемых файлов (PyInstaller) — папка рядом с exe
        base_path = Path(sys.executable).parent
    else:
        # Для обычного запуска — корень проекта (где лежит main.py)
        base_path = Path(__file__).parent

    return base_path / "resources" / relative_path


if __name__ == "__main__":
    # Включаем поддержку высокого DPI (масштабирование интерфейса)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # Единый шрифт для всего приложения
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    app.setStyle("Fusion")  # современный стиль

    # Устанавливаем иконку приложения (если файл существует)
    icon_path = get_resource_path("icons/app_icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Создаём и показываем главное окно
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
