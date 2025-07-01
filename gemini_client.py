from google import genai
from google.genai import types
import logging
from typing import List, Dict, Optional
from config import GEMINI_API_KEY, GEMINI_MODEL
from news_searcher import NewsSearcher

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Инициализируем новый клиент
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = GEMINI_MODEL
        self.news_searcher = None
        logger.info(f"Gemini client initialized with model: {GEMINI_MODEL}")
    
    def analyze_channel_style(self, posts: List[Dict]) -> Optional[str]:
        """Анализ стиля постов канала"""
        try:
            if not posts:
                return None

            # Подготавливаем текст постов для анализа
            posts_text = "\n\n---\n\n".join([post['content'] for post in posts[:30]])

            prompt = f"""
Проанализируй стиль написания постов в Telegram канале. Вот примеры постов:

{posts_text}

Проведи детальный анализ и опиши:
1. Тон и стиль общения (формальный/неформальный, дружелюбный/серьезный)
2. Структуру постов (как организован текст, используются ли списки, заголовки)
3. Длину постов (короткие/средние/длинные)
4. Использование эмодзи и их стиль
5. Тематику и направленность контента
6. Особенности языка (сленг, профессиональная лексика, простой язык)
7. Призывы к действию и взаимодействию с аудиторией
8. Форматирование текста (жирный, курсив, подчеркивание)

Результат должен быть структурированным описанием стиля, который можно использовать для генерации похожих постов.
"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)  # Отключаем thinking для скорости
                )
            )
            return response.text

        except Exception as e:
            logger.error(f"Error analyzing channel style: {e}")
            return None
    
    async def generate_post(self, style_analysis: str, topic: str = None, post_type: str = "general", include_news: bool = False) -> Optional[str]:
        """Генерация поста в стиле канала с возможностью включения новостей"""
        try:
            # Получаем актуальные новости если нужно
            news_context = ""
            if include_news and topic:
                news_context = await self._get_news_context(topic)

            if post_type == "random":
                topic_prompt = "Придумай интересную и актуальную тему для поста."
            elif post_type == "topic" and topic:
                topic_prompt = f"Тема поста: {topic}"
            elif post_type == "free" and topic:
                topic_prompt = f"Напиши пост на тему: {topic}"
            elif post_type == "news" and topic:
                topic_prompt = f"Создай пост на основе актуальных новостей по теме: {topic}"
            else:
                topic_prompt = "Создай интересный пост на актуальную тему."

            prompt = f"""
На основе анализа стиля канала создай новый пост:

АНАЛИЗ СТИЛЯ КАНАЛА:
{style_analysis}

ЗАДАНИЕ:
{topic_prompt}

{news_context}

ТРЕБОВАНИЯ:
1. Строго следуй выявленному стилю написания
2. Используй тот же тон и манеру общения
3. Соблюдай структуру и длину постов как в примерах
4. Используй эмодзи в том же стиле и количестве
5. Применяй такое же форматирование текста
6. Сохрани особенности языка и лексики
7. Если в стиле есть призывы к действию - включи их
8. Если предоставлены новости - используй их как основу для контента, но адаптируй под стиль канала

Создай ОДИН пост, готовый к публикации в Telegram канале.
"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            return response.text

        except Exception as e:
            logger.error(f"Error generating post: {e}")
            return None
    
    def improve_post(self, post_content: str, style_analysis: str, feedback: str) -> Optional[str]:
        """Улучшение поста на основе обратной связи"""
        try:
            prompt = f"""
Улучши этот пост на основе обратной связи:

ИСХОДНЫЙ ПОСТ:
{post_content}

СТИЛЬ КАНАЛА:
{style_analysis}

ОБРАТНАЯ СВЯЗЬ:
{feedback}

Перепиши пост, учитывая замечания и сохраняя стиль канала.
"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            return response.text

        except Exception as e:
            logger.error(f"Error improving post: {e}")
            return None
    
    async def generate_multiple_variants(self, style_analysis: str, topic: str, count: int = 3, include_news: bool = False) -> List[str]:
        """Генерация нескольких вариантов поста"""
        try:
            # Получаем новости если нужно
            news_context = ""
            if include_news:
                news_context = await self._get_news_context(topic)

            variants = []
            for i in range(count):
                prompt = f"""
На основе анализа стиля канала создай вариант #{i+1} поста:

АНАЛИЗ СТИЛЯ:
{style_analysis}

ТЕМА: {topic}

{news_context}

Создай уникальный пост, отличающийся от предыдущих вариантов, но в том же стиле.
Если предоставлены новости, используй разные аспекты или подходы к освещению темы.
"""
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=0)
                    )
                )
                if response.text:
                    variants.append(response.text)

            return variants

        except Exception as e:
            logger.error(f"Error generating multiple variants: {e}")
            return []

    async def _get_news_context(self, topic: str) -> str:
        """Получение контекста новостей по теме"""
        try:
            if not self.news_searcher:
                self.news_searcher = NewsSearcher()

            async with self.news_searcher as searcher:
                articles = await searcher.search_news_by_topic(topic, max_results=5)

            if not articles:
                return ""

            news_text = "АКТУАЛЬНЫЕ НОВОСТИ ПО ТЕМЕ:\n\n"
            for i, article in enumerate(articles, 1):
                news_text += f"{i}. {article.get('title', 'Без заголовка')}\n"
                if article.get('summary'):
                    news_text += f"   {article.get('summary')[:200]}...\n"
                news_text += f"   Источник: {article.get('source', 'Неизвестно')}\n\n"

            return news_text

        except Exception as e:
            logger.error(f"Error getting news context: {e}")
            return ""

    async def generate_news_based_post(self, style_analysis: str, topic: str) -> Optional[str]:
        """Генерация поста на основе актуальных новостей"""
        try:
            return await self.generate_post(
                style_analysis=style_analysis,
                topic=topic,
                post_type="news",
                include_news=True
            )
        except Exception as e:
            logger.error(f"Error generating news-based post: {e}")
            return None

    async def summarize_news(self, topic: str, max_articles: int = 5) -> Optional[str]:
        """Создание сводки новостей по теме"""
        try:
            if not self.news_searcher:
                self.news_searcher = NewsSearcher()

            async with self.news_searcher as searcher:
                articles = await searcher.search_news_by_topic(topic, max_articles)

            if not articles:
                return f"По теме '{topic}' актуальных новостей не найдено."

            # Формируем промпт для создания сводки
            articles_text = ""
            for i, article in enumerate(articles, 1):
                articles_text += f"{i}. {article.get('title', 'Без заголовка')}\n"
                if article.get('summary'):
                    articles_text += f"   {article.get('summary')}\n"
                articles_text += f"   Источник: {article.get('source', 'Неизвестно')}\n\n"

            prompt = f"""
Создай краткую и информативную сводку новостей по теме "{topic}":

{articles_text}

Требования:
1. Выдели основные тренды и события
2. Структурируй информацию логично
3. Используй эмодзи для лучшего восприятия
4. Сделай текст интересным и легко читаемым
5. Укажи ключевые факты и цифры
6. Объем: 200-300 слов

Создай сводку в формате для Telegram канала.
"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            return response.text

        except Exception as e:
            logger.error(f"Error summarizing news: {e}")
            return None
