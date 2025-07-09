import tempfile
import time
import webbrowser
from src.utils.logger_config import setup_logger

logger = setup_logger("telegram.log", __name__)


def send_telegram_message(token, chat_id, message):
    """Отправляет сообщение через Telegram"""
    logger.info(f"Попытка отправки сообщения в Telegram (chat_id: {chat_id})")
    logger.debug(f"Текст сообщения: {message}")

    if not token or not chat_id:
        error_msg = "⚠️ Не заданы настройки Telegram"
        logger.warning(error_msg)
        return error_msg

    try:
        full_message = f"<b>Screen Monitor</b>\n{message}\n<code>{time.strftime('%H:%M:%S')}</code>"
        logger.debug("Сформировано сообщение для Telegram")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Отправка сообщения Telegram Bot</title>
            <script>
                window.onload = function() {{
                    document.getElementById('telegramForm').submit();
                }};
            </script>
        </head>
        <body>
            <form id="telegramForm" action="https://api.telegram.org/bot{token}/sendMessage" method="POST" style="display:none;">
                <input type="text" name="chat_id" value="{chat_id}">
                <textarea name="text">{full_message}</textarea>
                <input type="hidden" name="parse_mode" value="HTML">
            </form>
        </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html", encoding="utf-8") as f:
            f.write(html_content)
            temp_filename = f.name
            logger.debug(f"Создан временный HTML-файл: {temp_filename}")

        webbrowser.open(f"file://{temp_filename}")
        success_msg = "Сообщение отправлено через браузер"
        logger.info(success_msg)
        return success_msg

    except Exception as e:
        error_msg = f"⚠️ Ошибка при отправке в Telegram: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


def test_telegram_connection(token, chat_id):
    """Тестирует соединение с Telegram"""
    logger.info(f"Тестирование соединения с Telegram (chat_id: {chat_id})")

    if not token or not chat_id:
        error_msg = "⚠️ Введите токен и chat_id!"
        logger.warning(error_msg)
        return error_msg

    try:
        test_message = "🟢 Тестовое уведомление от Screen Monitor"
        full_message = f"<b>Screen Monitor</b>\n{test_message}\n<code>{time.strftime('%H:%M:%S')}</code>"
        logger.debug("Сформировано тестовое сообщение")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Тест отправки Telegram Bot</title>
            <script>
                window.onload = function() {{
                    document.getElementById('telegramForm').submit();
                }};
            </script>
        </head>
        <body>
            <div style="font-family: Arial; padding: 20px; text-align: center;">
                <h1>Тест отправки Telegram Bot</h1>
                <p>Автоматическая отправка тестового сообщения...</p>
                <form id="telegramForm" action="https://api.telegram.org/bot{token}/sendMessage" method="POST">
                    <input type="hidden" name="chat_id" value="{chat_id}">
                    <textarea name="text" style="display:none;">{full_message}</textarea>
                    <input type="hidden" name="parse_mode" value="HTML">
                </form>
            </div>
        </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html", encoding="utf-8") as f:
            f.write(html_content)
            temp_filename = f.name
            logger.debug(f"Создан временный тестовый HTML-файл: {temp_filename}")

        webbrowser.open(f"file://{temp_filename}")
        success_msg = "Тестовая форма отправки открыта в браузере"
        logger.info(success_msg)
        return success_msg

    except Exception as e:
        error_msg = f"⚠️ Ошибка при тестировании Telegram: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg
