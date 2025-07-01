#!/usr/bin/env python3
"""
Примеры использования компонентов PostAI Bot
"""

import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def example_database_usage():
    """Пример работы с базой данных"""
    print("📊 Пример работы с базой данных")
    print("-" * 30)
    
    from database import Database
    
    # Создаем экземпляр базы данных
    db = Database()
    
    # Добавляем пользователя
    user_added = db.add_user(
        user_id=123456789,
        username="example_user",
        first_name="Иван",
        last_name="Иванов"
    )
    print(f"Пользователь добавлен: {user_added}")
    
    # Добавляем канал
    channel_added = db.add_channel(
        channel_id=-1001234567890,
        channel_name="Пример канала",
        channel_username="example_channel",
        user_id=123456789
    )
    print(f"Канал добавлен: {channel_added}")
    
    # Получаем каналы пользователя
    channels = db.get_user_channels(123456789)
    print(f"Каналов найдено: {len(channels)}")
    for channel in channels:
        print(f"  - {channel['channel_name']} (ID: {channel['channel_id']})")
    
    # Добавляем тестовые посты
    test_posts = [
        {
            'post_id': 1,
            'content': 'Привет! Это первый тестовый пост 👋',
            'date': '2024-01-01 12:00:00'
        },
        {
            'post_id': 2,
            'content': 'Сегодня отличная погода для изучения новых технологий! 🌟',
            'date': '2024-01-02 15:30:00'
        },
        {
            'post_id': 3,
            'content': 'Делимся полезными советами по программированию 💻',
            'date': '2024-01-03 09:15:00'
        }
    ]
    
    posts_added = db.add_posts(-1001234567890, test_posts)
    print(f"Посты добавлены: {posts_added}")
    
    # Получаем посты канала
    posts = db.get_channel_posts(-1001234567890)
    print(f"Постов получено: {len(posts)}")
    
    print("✅ Пример работы с базой данных завершен\n")

async def example_gemini_usage():
    """Пример работы с Gemini AI"""
    print("🧠 Пример работы с Gemini AI")
    print("-" * 30)

    # Проверяем наличие API ключа
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY не найден в переменных окружения")
        print("💡 Добавьте ключ в файл .env для тестирования")
        return

    try:
        from gemini_client import GeminiClient

        # Создаем клиент
        gemini = GeminiClient()
        print("✅ Gemini клиент инициализирован (Gemini 2.5 Flash)")

        # Тестовые посты для анализа
        test_posts = [
            {
                'content': 'Привет, друзья! 👋 Сегодня хочу поделиться с вами интересной новостью из мира технологий.',
                'date': '2024-01-01'
            },
            {
                'content': '🚀 Запускаем новый проект! Это будет что-то невероятное. Следите за обновлениями!',
                'date': '2024-01-02'
            },
            {
                'content': '💡 Совет дня: всегда изучайте что-то новое. Знания - это сила! 📚',
                'date': '2024-01-03'
            }
        ]

        print("🔍 Анализирую стиль постов...")
        style_analysis = gemini.analyze_channel_style(test_posts)

        if style_analysis:
            print("✅ Анализ стиля завершен:")
            print(f"📝 Результат: {style_analysis[:200]}...")

            print("\n🎯 Генерирую обычный пост по теме...")
            generated_post = await gemini.generate_post(
                style_analysis=style_analysis,
                topic="искусственный интеллект",
                post_type="topic"
            )

            if generated_post:
                print("✅ Обычный пост сгенерирован:")
                print(f"📄 {generated_post[:200]}...")
            else:
                print("❌ Ошибка генерации обычного поста")

            print("\n📰 Генерирую пост с новостями...")
            news_post = await gemini.generate_news_based_post(
                style_analysis=style_analysis,
                topic="технологии"
            )

            if news_post:
                print("✅ Пост с новостями сгенерирован:")
                print(f"📄 {news_post[:200]}...")
            else:
                print("❌ Ошибка генерации поста с новостями")

            print("\n📊 Создаю сводку новостей...")
            news_summary = await gemini.summarize_news("искусственный интеллект", 3)

            if news_summary:
                print("✅ Сводка новостей создана:")
                print(f"📄 {news_summary[:200]}...")
            else:
                print("❌ Ошибка создания сводки новостей")
        else:
            print("❌ Ошибка анализа стиля")

    except Exception as e:
        print(f"❌ Ошибка при работе с Gemini: {e}")

    print("✅ Пример работы с Gemini AI завершен\n")

async def example_news_search():
    """Пример работы с поиском новостей"""
    print("📰 Пример работы с поиском новостей")
    print("-" * 30)

    try:
        from news_searcher import NewsSearcher

        async with NewsSearcher() as searcher:
            print("✅ NewsSearcher инициализирован")

            # Поиск новостей по теме
            print("🔍 Ищу новости по теме 'искусственный интеллект'...")
            articles = await searcher.search_news_by_topic("искусственный интеллект", max_results=3)

            if articles:
                print(f"✅ Найдено {len(articles)} статей:")
                for i, article in enumerate(articles, 1):
                    print(f"  {i}. {article.get('title', 'Без заголовка')}")
                    print(f"     Источник: {article.get('source', 'Неизвестно')}")
                    if article.get('published'):
                        print(f"     Дата: {article['published']}")
                    print()
            else:
                print("❌ Новости не найдены")

            # Получение последних новостей
            print("📊 Получаю последние новости...")
            latest_news = await searcher.get_latest_news(max_results=3)

            if latest_news:
                print(f"✅ Получено {len(latest_news)} последних новостей:")
                for i, article in enumerate(latest_news, 1):
                    print(f"  {i}. {article.get('title', 'Без заголовка')}")
                    print(f"     Источник: {article.get('source', 'Неизвестно')}")
                    print()
            else:
                print("❌ Последние новости не получены")

            # Форматирование новостей
            if articles:
                print("📝 Форматирую новости для отправки...")
                formatted_summary = searcher.format_news_summary(articles, max_articles=3)
                print("✅ Отформатированная сводка:")
                print(formatted_summary[:300] + "...")

    except Exception as e:
        print(f"❌ Ошибка при работе с поиском новостей: {e}")

    print("✅ Пример работы с поиском новостей завершен\n")

async def example_post_generator():
    """Пример работы с генератором постов"""
    print("✨ Пример работы с генератором постов")
    print("-" * 30)
    
    # Проверяем наличие API ключа
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY не найден для тестирования генератора")
        return
    
    try:
        from post_generator import PostGenerator
        from database import Database
        
        # Инициализируем компоненты
        db = Database()
        generator = PostGenerator()
        
        # Создаем тестовые данные
        channel_id = -1001234567890
        
        # Сохраняем тестовый анализ стиля
        test_style = """
        Стиль канала: дружелюбный и мотивирующий
        Тон: позитивный, вдохновляющий
        Эмодзи: часто используются 🚀 💡 ✨ 👋
        Структура: короткие абзацы, призывы к действию
        Длина: средние посты (100-200 слов)
        """
        
        db.save_style_analysis(channel_id, test_style, 10)
        print("✅ Тестовый анализ стиля сохранен")
        
        # Генерируем пост по теме
        print("🎯 Генерирую пост по теме...")
        result = generator.generate_post_by_topic(channel_id, "машинное обучение")
        
        if result['success']:
            print("✅ Пост по теме сгенерирован:")
            print(f"📄 {result['post'][:200]}...")
        else:
            print(f"❌ Ошибка: {result['error']}")
        
        # Генерируем случайный пост
        print("\n🎲 Генерирую случайный пост...")
        result = generator.generate_random_post(channel_id)
        
        if result['success']:
            print("✅ Случайный пост сгенерирован:")
            print(f"📄 {result['post'][:200]}...")
        else:
            print(f"❌ Ошибка: {result['error']}")
            
    except Exception as e:
        print(f"❌ Ошибка при работе с генератором: {e}")
    
    print("✅ Пример работы с генератором постов завершен\n")

async def example_full_workflow():
    """Пример полного рабочего процесса"""
    print("🔄 Пример полного рабочего процесса")
    print("-" * 30)
    
    try:
        # 1. Инициализация компонентов
        from database import Database
        from post_generator import PostGenerator
        
        db = Database()
        generator = PostGenerator()
        
        print("1️⃣ Компоненты инициализированы")
        
        # 2. Добавление пользователя
        user_id = 987654321
        db.add_user(user_id, "workflow_user", "Тест", "Пользователь")
        print("2️⃣ Пользователь добавлен")
        
        # 3. Добавление канала
        channel_id = -1009876543210
        db.add_channel(channel_id, "Тестовый канал", user_id, "test_workflow")
        print("3️⃣ Канал добавлен")
        
        # 4. Добавление постов
        workflow_posts = [
            {
                'post_id': 101,
                'content': '🌟 Добро пожаловать в наш канал! Здесь мы делимся самыми интересными новостями.',
                'date': '2024-01-01 10:00:00'
            },
            {
                'post_id': 102,
                'content': '💡 Сегодняшний совет: никогда не переставайте учиться! Знания открывают новые возможности.',
                'date': '2024-01-02 14:30:00'
            },
            {
                'post_id': 103,
                'content': '🚀 Запускаем новую серию постов о технологиях будущего. Будет интересно!',
                'date': '2024-01-03 16:45:00'
            }
        ]
        
        db.add_posts(channel_id, workflow_posts)
        print("4️⃣ Посты добавлены")
        
        # 5. Проверка данных
        channels = db.get_user_channels(user_id)
        posts = db.get_channel_posts(channel_id)
        
        print(f"5️⃣ Данные проверены: {len(channels)} каналов, {len(posts)} постов")
        
        # 6. Имитация анализа (без реального API)
        mock_analysis = """
        Анализ стиля канала:
        - Дружелюбный и позитивный тон
        - Использование эмодзи в начале постов
        - Мотивирующий контент
        - Короткие, легко читаемые сообщения
        """
        
        db.save_style_analysis(channel_id, mock_analysis, len(posts))
        print("6️⃣ Анализ стиля сохранен")
        
        # 7. Получение информации о стиле
        style_info = db.get_style_analysis(channel_id)
        if style_info:
            print(f"7️⃣ Стиль получен: {style_info['posts_count']} постов проанализировано")
        
        print("✅ Полный рабочий процесс завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка в рабочем процессе: {e}")

async def main():
    """Главная функция с примерами"""
    print("🤖 PostAI Bot - Примеры использования (обновленная версия)")
    print("=" * 60)

    # Запускаем примеры
    await example_database_usage()
    await example_news_search()
    await example_gemini_usage()
    await example_post_generator()
    await example_full_workflow()

    print("🎉 Все примеры завершены!")
    print("💡 Для полного тестирования добавьте GEMINI_API_KEY в .env файл")
    print("📰 Новые функции: поиск новостей, генерация с новостями, сводки новостей")
    print("🧠 Обновлено: Gemini 2.5 Flash, новый SDK")

if __name__ == "__main__":
    asyncio.run(main())
