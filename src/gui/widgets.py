from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QGroupBox, QLabel, QPushButton, QStyle, QToolButton, QWidget, QHBoxLayout


class RoundedGroupBox(QGroupBox):
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
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(32)
        self.setStyleSheet("background-color: #292a2d;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        self.icon_label.setPixmap(QIcon(self.style().standardIcon(QStyle.SP_ComputerIcon)).pixmap(24, 24))
        layout.addWidget(self.icon_label)

        self.title = QLabel("Screen Monitor")
        self.title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.title.setStyleSheet("color: #f8faff;")
        layout.addWidget(self.title)

        layout.addStretch()

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

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent.drag_position = event.globalPos() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.parent.move(event.globalPos() - self.parent.drag_position)
            event.accept()
