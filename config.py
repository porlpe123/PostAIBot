import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Google AI Studio API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Database settings
DATABASE_PATH = 'bot_database.db'

# Bot settings
MAX_POSTS_TO_ANALYZE = 50
MIN_POSTS_FOR_ANALYSIS = 5
GEMINI_MODEL = 'gemini-2.5-flash'

# News search settings
MAX_NEWS_ARTICLES = 10
NEWS_SEARCH_TIMEOUT = 30
ENABLE_NEWS_SEARCH = True

# RSS News sources
RSS_SOURCES = [
    'https://feeds.bbci.co.uk/news/rss.xml',
    'https://rss.cnn.com/rss/edition.rss',
    'https://www.reuters.com/rssFeed/worldNews',
    'https://techcrunch.com/feed/',
    'https://habr.com/ru/rss/hub/artificial_intelligence/',
    'https://lenta.ru/rss'
]

# Messages
WELCOME_MESSAGE = """
🤖 Добро пожаловать в PostAI Bot!

Этот бот поможет вам генерировать посты в стиле вашего Telegram канала.

Как это работает:
1️⃣ Добавьте бота в ваш канал как администратора
2️⃣ Бот проанализирует стиль ваших постов
3️⃣ Генерируйте новые посты в том же стиле!

Нажмите /start чтобы начать 🚀
"""

HELP_MESSAGE = """
📖 Помощь по использованию бота:

🔹 /start - Начать работу с ботом
🔹 /help - Показать это сообщение
🔹 /channels - Управление каналами
🔹 /generate - Генерация постов
🔹 /settings - Настройки

💡 Для работы бота добавьте его в канал как администратора с правами чтения сообщений.
"""

# Keyboard layouts
MAIN_MENU_KEYBOARD = [
    ["📊 Мои каналы", "✨ Генерировать пост"],
    ["⚙️ Настройки", "❓ Помощь"]
]

CHANNELS_MENU_KEYBOARD = [
    ["➕ Добавить канал", "📋 Список каналов"],
    ["🔄 Обновить анализ", "🏠 Главное меню"]
]

GENERATE_MENU_KEYBOARD = [
    ["🎯 По теме", "🎲 Случайный пост"],
    ["📝 Свободная тема", "📰 С новостями"],
    ["📊 Сводка новостей", "🏠 Главное меню"]
]
