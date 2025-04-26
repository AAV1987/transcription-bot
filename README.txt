=== Как запустить бота ===

1. Установить Python 3.10+
2. Установить зависимости:
    pip install -r requirements.txt

3. Установить ffmpeg:
    sudo apt install ffmpeg  (Linux)
    brew install ffmpeg (Mac)

4. Создать бота в Telegram через @BotFather и получить TELEGRAM_TOKEN.

5. Получить OpenAI API KEY на https://platform.openai.com/account/api-keys

6. Создать переменные окружения:
   TELEGRAM_TOKEN=твой_токен
   OPENAI_API_KEY=твой_ключ

7. Запустить локально:
    python bot.py

8. Для деплоя:
    - Залить проект на GitHub
    - Подключить к Railway.app
    - Добавить переменные окружения
    - Deploy

Бот принимает голосовые, аудиофайлы и видео, возвращает распознанный текст в PDF.