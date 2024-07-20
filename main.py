
import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import filters as Filters
import speech_recognition as sr
from pydub import AudioSegment
from pathlib import Path

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ваш токен, который вы получили от BotFather
TOKEN = '6764986227:AAHgdWBgIFoDQoKQGe8xSIvShZvxdRwie2s'

# Инициализация распознавателя речи
recognizer = sr.Recognizer()

async def start(update: Update, context: CallbackContext) -> None:
    """Отправляет приветственное сообщение при старте бота"""
    await update.message.reply_text('Привет! Пришли мне голосовое сообщение, и я верну его текст!')

async def update_progress_message(context: CallbackContext, chat_id: int, message_id: int, progress: int) -> None:
    """Обновляет сообщение прогресса"""
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f'Обработка аудио: {progress}%'
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении сообщения прогресса: {e}")

async def voice_handler(update: Update, context: CallbackContext) -> None:
    """Обрабатывает голосовые сообщения"""
    file = await update.message.voice.get_file()

    # Скачиваем аудиофайл
    file_path = await file.download_to_drive()
    file_path = Path(file_path)

    # Конвертируем ogg в wav
    audio = AudioSegment.from_file(file_path, format='ogg')
    wav_path = file_path.with_suffix('.wav')
    audio.export(wav_path, format='wav')

    # Отправляем начальное сообщение о прогрессе
    progress_message = await update.message.reply_text('Обработка аудио: 0%')
    chat_id = update.message.chat_id
    message_id = progress_message.message_id

    # Распознаем речь
    with sr.AudioFile(str(wav_path)) as source:
        audio_data = recognizer.record(source)
        total_duration = len(audio) / 1000  # в секундах
        progress_update_interval = 1  # интервал обновления прогресса в секундах

        for i in range(0, int(total_duration), progress_update_interval):
            await asyncio.sleep(progress_update_interval)
            progress = min(int((i / total_duration) * 100), 100)
            await update_progress_message(context, chat_id, message_id, progress)

        try:
            text = recognizer.recognize_google(audio_data, language='ru-RU')
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f'Распознанный текст: {text}'
            )
        except sr.UnknownValueError:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text='Не удалось распознать аудио.'
            )
        except sr.RequestError:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text='Ошибка сервиса распознавания.'

            )
    # Удаляем временные файлы
    os.remove(file_path)
    os.remove(wav_path)

def main() -> None:
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(Filters.VOICE, voice_handler))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()

