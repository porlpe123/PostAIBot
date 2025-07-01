import google.generativeai as genai
import logging
from typing import List, Dict, Optional
from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
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
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error analyzing channel style: {e}")
            return None
    
    def generate_post(self, style_analysis: str, topic: str = None, post_type: str = "general") -> Optional[str]:
        """Генерация поста в стиле канала"""
        try:
            if post_type == "random":
                topic_prompt = "Придумай интересную и актуальную тему для поста."
            elif post_type == "topic" and topic:
                topic_prompt = f"Тема поста: {topic}"
            elif post_type == "free" and topic:
                topic_prompt = f"Напиши пост на тему: {topic}"
            else:
                topic_prompt = "Создай интересный пост на актуальную тему."
            
            prompt = f"""
На основе анализа стиля канала создай новый пост:

АНАЛИЗ СТИЛЯ КАНАЛА:
{style_analysis}

ЗАДАНИЕ:
{topic_prompt}

ТРЕБОВАНИЯ:
1. Строго следуй выявленному стилю написания
2. Используй тот же тон и манеру общения
3. Соблюдай структуру и длину постов как в примерах
4. Используй эмодзи в том же стиле и количестве
5. Применяй такое же форматирование текста
6. Сохрани особенности языка и лексики
7. Если в стиле есть призывы к действию - включи их

Создай ОДИН пост, готовый к публикации в Telegram канале.
"""
            
            response = self.model.generate_content(prompt)
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
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error improving post: {e}")
            return None
    
    def generate_multiple_variants(self, style_analysis: str, topic: str, count: int = 3) -> List[str]:
        """Генерация нескольких вариантов поста"""
        try:
            variants = []
            for i in range(count):
                prompt = f"""
На основе анализа стиля канала создай вариант #{i+1} поста:

АНАЛИЗ СТИЛЯ:
{style_analysis}

ТЕМА: {topic}

Создай уникальный пост, отличающийся от предыдущих вариантов, но в том же стиле.
"""
                response = self.model.generate_content(prompt)
                if response.text:
                    variants.append(response.text)
            
            return variants
            
        except Exception as e:
            logger.error(f"Error generating multiple variants: {e}")
            return []
