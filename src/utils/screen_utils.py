from mss import mss
from PyQt5.QtWidgets import QApplication


def get_physical_area(logical_area):
    """
    Преобразует логические координаты области (в пикселях Qt) в физические пиксели
    с учётом масштабирования экрана (devicePixelRatio) и смещения мониторов.

    :param logical_area: Словарь с ключами left, top, width, height (логические координаты)
    :return: Словарь с теми же ключами, но с физическими координатами (int)
    """
    screen = QApplication.primaryScreen()
    scale = screen.devicePixelRatio()

    with mss() as sct:
        monitors = sct.monitors[1:]  # пропускаем общую область
        min_left = min(m["left"] for m in monitors)

    return {
        "left": int((logical_area["left"] + min_left) * scale),
        "top": int(logical_area["top"] * scale),
        "width": int(logical_area["width"] * scale),
        "height": int(logical_area["height"] * scale),
    }
