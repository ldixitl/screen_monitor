import os
import tempfile
import time
import webbrowser

from dotenv import load_dotenv

from src.utils.logger_config import setup_logger

logger = setup_logger("telegram.log", __name__)

# Загружаем переменные окружения (токен может быть переопределён в .env)
load_dotenv()

# Токен Вашего Telegram-бота.
# Можно задать через переменную окружения TELEGRAM_BOT_TOKEN или используйте фиксированный.
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def send_telegram_message(chat_id, message):
    """
    Отправляет сообщение в Telegram через чат-бота.

    Из-за ограничений CORS при прямых запросах из Python (если нет прокси), функция создаёт временный HTML-файл
    с JavaScript, который отправляет запрос к API Telegram, и открывает его в браузере. Это надёжный способ обойти
    блокировки и не требует установки дополнительных библиотек.

    :param chat_id: ID чата (пользователя) в Telegram (строка).
    :param message: Текст сообщения (строка).
    :return: Строка с результатом операции (для отображения в интерфейсе).
    """
    logger.info(f"Попытка отправки сообщения в Telegram (chat_id: {chat_id})")
    logger.debug(f"Текст сообщения: {message}")

    if not chat_id:
        error_msg = "⚠️ Не задан Telegram ID"
        logger.warning(error_msg)
        return error_msg

    try:
        # Формируем сообщение с HTML-разметкой
        full_message = f"<b>Screen Monitor</b>\n{message}\n<code>{time.strftime('%H:%M:%S')}</code>"
        logger.debug("Сформировано сообщение для Telegram")

        # Создаём HTML-страницу с индикатором загрузки и JS-запросом к Telegram API
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    background-color: #212327;
                    color: #f8faff;
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    text-align: center;
                    padding: 20px;
                    border-radius: 8px;
                    background-color: #292a2d;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    max-width: 80%;
                }}
                .loader {{
                    border: 3px solid #292a2d;
                    border-top: 3px solid #4d6bfe;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 15px;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                .success {{
                    color: #4d6bfe;
                }}
                .error {{
                    color: #ff6b6b;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="loader"></div>
                <p>Отправка сообщения в Telegram...</p>
            </div>

            <script>
            window.onload = function() {{
                const container = document.querySelector('.container');
                const message = `{full_message.replace('`', '\\`')}`;

                fetch('https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                    body: `chat_id={chat_id}&text=${{encodeURIComponent(message)}}&parse_mode=HTML`
                }})
                .then(response => response.json())
                .then(data => {{
                    if(data.ok) {{
                        container.innerHTML = '<p class="success">Сообщение успешно отправлено</p>';
                        setTimeout(window.close, 800);
                    }} else {{
                        container.innerHTML = `<p class="error">Ошибка Telegram: ${{data.description || 'Неизвестная ошибка'}}</p>`;
                    }}
                }})
                .catch(e => {{
                    container.innerHTML = `<p class="error">Ошибка сети: ${{e.message}}</p>`;
                }});
            }};
            </script>
        </body>
        </html>
        """

        # Сохраняем HTML во временный файл
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html", encoding="utf-8") as f:
            f.write(html_content)
            temp_filename = f.name
            logger.debug(f"Создан временный HTML-файл: {temp_filename}")

        # Открываем файл в браузере по умолчанию
        webbrowser.open(f"file://{temp_filename}")
        success_msg = "Сообщение отправлено через браузер"
        logger.info(success_msg)
        return success_msg

    except Exception as e:
        error_msg = f"⚠️ Ошибка при отправке в Telegram: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg
