#!/usr/bin/env python3
"""
Простой скрипт для запуска PostAI Bot
"""

import os
import sys

def check_requirements():
    """Проверка наличия необходимых файлов и переменных"""
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("📝 Создайте файл .env на основе .env.example")
        print("💡 Команда: cp .env.example .env")
        return False
    
    # Проверяем переменные окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    if not telegram_token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!")
        print("🤖 Получите токен у @BotFather в Telegram")
        return False
    
    if not gemini_key:
        print("❌ GEMINI_API_KEY не найден в .env файле!")
        print("🧠 Получите ключ на https://aistudio.google.com/")
        return False
    
    print("✅ Все переменные окружения настроены правильно")
    return True

def main():
    """Главная функция запуска"""
    print("🤖 PostAI Bot Launcher")
    print("=" * 30)
    
    # Проверяем требования
    if not check_requirements():
        print("\n❌ Проверьте настройки и попробуйте снова")
        sys.exit(1)
    
    print("🚀 Запускаю бота...")
    print("📝 Логи сохраняются в bot.log")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print("=" * 30)
    
    # Запускаем основной модуль
    try:
        import main
        import asyncio
        asyncio.run(main.main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("📦 Установите зависимости: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
