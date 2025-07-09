import sys

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

from src.gui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Настройки шрифта
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    app.setStyle("Fusion")

    # Главное окно
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
