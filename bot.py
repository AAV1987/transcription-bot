
import os
import logging
import aiohttp
import asyncio
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from fpdf import FPDF
import openai

# Конфигурация через переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
openai.api_key = OPENAI_API_KEY

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

async def download_file(file_id: str, destination: str):
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(destination, 'wb') as f:
                    f.write(await resp.read())
            else:
                raise Exception(f"Не удалось скачать файл: {resp.status}")

def convert_to_wav(input_path: str, output_path: str):
    subprocess.run(['ffmpeg', '-y', '-i', input_path, '-ar', '16000', '-ac', '1', output_path], check=True)

async def transcribe_and_translate(file_path: str) -> str:
    with open(file_path, 'rb') as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    original_text = transcript['text']
    if not any("\u0400" <= ch <= "\u04FF" for ch in original_text):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Переведи текст на русский язык максимально естественно."},
                {"role": "user", "content": original_text}
            ],
            temperature=0.3,
        )
        translated_text = completion['choices'][0]['message']['content']
        return translated_text.strip()
    return original_text.strip()

def save_text_to_pdf(text: str, pdf_path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(pdf_path)

async def process_media(file: types.File, file_id: str, extension: str):
    input_path = os.path.join(TEMP_DIR, f"{file_id}.{extension}")
    wav_path = os.path.join(TEMP_DIR, f"{file_id}.wav")
    pdf_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
    try:
        await download_file(file.file_id, input_path)
        convert_to_wav(input_path, wav_path)
        text = await transcribe_and_translate(wav_path)
        save_text_to_pdf(text, pdf_path)
        return text, pdf_path
    finally:
        for path in (input_path, wav_path):
            if os.path.exists(path):
                os.remove(path)

@dp.message_handler(content_types=[types.ContentType.VOICE, types.ContentType.AUDIO, types.ContentType.VIDEO])
async def handle_audio_video(message: types.Message):
    await message.reply("Файл получен. Обрабатываю...")
    try:
        file = None
        extension = 'ogg'
        if message.voice:
            file = message.voice
            extension = 'ogg'
        elif message.audio:
            file = message.audio
            extension = message.audio.file_name.split('.')[-1].lower() if message.audio.file_name else 'mp3'
        elif message.video:
            file = message.video
            extension = 'mp4'
        if not file:
            await message.reply("Не удалось определить тип файла.")
            return
        text, pdf_path = await process_media(file, file.file_id, extension)
        await message.reply("Текст успешно распознан! Отправляю файл PDF...")
        await message.reply_document(types.InputFile(pdf_path))
    except Exception as e:
        logging.exception("Ошибка при обработке файла")
        await message.reply("Произошла ошибка при обработке. Попробуй отправить другой файл.")
    finally:
        pdf_temp = os.path.join(TEMP_DIR, f"{message.voice.file_id if message.voice else message.audio.file_id if message.audio else message.video.file_id}.pdf")
        if os.path.exists(pdf_temp):
            os.remove(pdf_temp)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
