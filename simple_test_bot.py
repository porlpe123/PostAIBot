#!/usr/bin/env python3
"""
Простой тестовый бот для диагностики проблем
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    keyboard = [
        ["📊 Тест", "🔍 Диагностика"],
        ["➕ Добавить канал", "❓ Помощь"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = f"""
🤖 Тестовый бот работает!

👋 Привет, {user.first_name}!

Этот бот создан для диагностики проблем.

Доступные команды:
/start - Начать
/debug - Диагностика
/test - Тест

Ваш ID: {user.id}
"""
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда диагностики"""
    user = update.effective_user
    
    debug_info = f"""
🔍 Диагностическая информация:

👤 Пользователь:
- ID: {user.id}
- Username: @{user.username or 'не указан'}
- Имя: {user.first_name}
- Фамилия: {user.last_name or 'не указана'}

💬 Сообщение:
- Тип чата: {update.effective_chat.type}
- ID чата: {update.effective_chat.id}

🤖 Бот:
- Статус: ✅ Работает
- Токен: {'✅ Настроен' if TOKEN else '❌ Не найден'}

📝 Логи сохраняются в консоль
"""
    
    await update.message.reply_text(debug_info)

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда"""
    await update.message.reply_text(
        "✅ Тест пройден! Бот отвечает на команды.\n\n"
        "Теперь попробуйте отправить ID канала или переслать сообщение."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений"""
    user = update.effective_user
    message_text = update.message.text
    
    logger.info(f"Получено сообщение от {user.id}: {message_text}")
    
    # Проверяем, если это пересланное сообщение
    if update.message.forward_from_chat:
        chat = update.message.forward_from_chat
        response = f"""
📤 Получено пересланное сообщение!

📊 Информация о канале:
- Название: {chat.title}
- ID: {chat.id}
- Тип: {chat.type}
- Username: @{chat.username or 'не указан'}

✅ Бот правильно обрабатывает пересланные сообщения!
"""
        await update.message.reply_text(response)
        return
    
    # Проверяем, если это ID канала
    if message_text and (message_text.startswith('-100') or message_text.lstrip('-').isdigit()):
        try:
            channel_id = int(message_text)
            response = f"""
🆔 Получен ID канала: {channel_id}

✅ Бот правильно обрабатывает ID каналов!

Следующий шаг: проверка доступа к каналу...
"""
            await update.message.reply_text(response)
            
            # Пробуем получить информацию о канале
            try:
                chat = await context.bot.get_chat(channel_id)
                success_response = f"""
✅ Успешно получена информация о канале!

📊 Канал: {chat.title}
👥 Тип: {chat.type}
🔗 Username: @{chat.username or 'не указан'}

🎉 Бот имеет доступ к каналу!
"""
                await update.message.reply_text(success_response)
            except Exception as e:
                error_response = f"""
❌ Ошибка доступа к каналу:
{str(e)}

🔧 Возможные причины:
1. Бот не добавлен в канал
2. У бота нет прав администратора
3. Неверный ID канала
"""
                await update.message.reply_text(error_response)
        except ValueError:
            await update.message.reply_text("❌ Неверный формат ID канала")
        return
    
    # Обработка кнопок меню
    if message_text == "📊 Тест":
        await test_command(update, context)
    elif message_text == "🔍 Диагностика":
        await debug_command(update, context)
    elif message_text == "➕ Добавить канал":
        await update.message.reply_text(
            "📝 Отправьте ID канала (например: -1001234567890)\n"
            "или перешлите сообщение из канала"
        )
    elif message_text == "❓ Помощь":
        await update.message.reply_text(
            "🆘 Помощь:\n\n"
            "1. Отправьте /start для начала\n"
            "2. Используйте /debug для диагностики\n"
            "3. Отправьте ID канала для тестирования\n"
            "4. Перешлите сообщение из канала"
        )
    else:
        # Эхо для любого другого сообщения
        await update.message.reply_text(
            f"📝 Получено сообщение: {message_text}\n\n"
            "✅ Бот работает и отвечает на сообщения!"
        )

async def main():
    """Главная функция"""
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!")
        return
    
    print("🤖 Запуск тестового бота...")
    print(f"🔑 Токен: {TOKEN[:10]}...")
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("debug", debug_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    # Запускаем бота
    print("✅ Тестовый бот запущен!")
    print("📱 Попробуйте отправить /start в Telegram")
    
    await application.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Тестовый бот остановлен")
