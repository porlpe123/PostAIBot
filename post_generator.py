import logging
from typing import List, Dict, Optional
from database import Database
from gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class PostGenerator:
    def __init__(self):
        self.db = Database()
        self.gemini = GeminiClient()
    
    def generate_post_by_topic(self, channel_id: int, topic: str) -> Dict:
        """Генерация поста по заданной теме"""
        try:
            # Получаем анализ стиля канала
            style_info = self.db.get_style_analysis(channel_id)
            
            if not style_info or not style_info['style_analysis']:
                return {
                    'success': False,
                    'error': 'Анализ стиля канала не найден. Сначала проанализируйте канал.'
                }
            
            # Генерируем пост
            generated_post = self.gemini.generate_post(
                style_analysis=style_info['style_analysis'],
                topic=topic,
                post_type="topic"
            )
            
            if not generated_post:
                return {
                    'success': False,
                    'error': 'Ошибка при генерации поста'
                }
            
            return {
                'success': True,
                'post': generated_post,
                'topic': topic,
                'channel_id': channel_id
            }
            
        except Exception as e:
            logger.error(f"Error generating post by topic: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_random_post(self, channel_id: int) -> Dict:
        """Генерация случайного поста"""
        try:
            style_info = self.db.get_style_analysis(channel_id)
            
            if not style_info or not style_info['style_analysis']:
                return {
                    'success': False,
                    'error': 'Анализ стиля канала не найден'
                }
            
            generated_post = self.gemini.generate_post(
                style_analysis=style_info['style_analysis'],
                post_type="random"
            )
            
            if not generated_post:
                return {
                    'success': False,
                    'error': 'Ошибка при генерации случайного поста'
                }
            
            return {
                'success': True,
                'post': generated_post,
                'topic': 'Случайная тема',
                'channel_id': channel_id
            }
            
        except Exception as e:
            logger.error(f"Error generating random post: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_free_topic_post(self, channel_id: int, user_request: str) -> Dict:
        """Генерация поста по свободной теме"""
        try:
            style_info = self.db.get_style_analysis(channel_id)
            
            if not style_info or not style_info['style_analysis']:
                return {
                    'success': False,
                    'error': 'Анализ стиля канала не найден'
                }
            
            generated_post = self.gemini.generate_post(
                style_analysis=style_info['style_analysis'],
                topic=user_request,
                post_type="free"
            )
            
            if not generated_post:
                return {
                    'success': False,
                    'error': 'Ошибка при генерации поста'
                }
            
            return {
                'success': True,
                'post': generated_post,
                'topic': user_request,
                'channel_id': channel_id
            }
            
        except Exception as e:
            logger.error(f"Error generating free topic post: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_multiple_variants(self, channel_id: int, topic: str, count: int = 3) -> Dict:
        """Генерация нескольких вариантов поста"""
        try:
            style_info = self.db.get_style_analysis(channel_id)
            
            if not style_info or not style_info['style_analysis']:
                return {
                    'success': False,
                    'error': 'Анализ стиля канала не найден'
                }
            
            variants = self.gemini.generate_multiple_variants(
                style_analysis=style_info['style_analysis'],
                topic=topic,
                count=count
            )
            
            if not variants:
                return {
                    'success': False,
                    'error': 'Ошибка при генерации вариантов постов'
                }
            
            return {
                'success': True,
                'variants': variants,
                'topic': topic,
                'channel_id': channel_id,
                'count': len(variants)
            }
            
        except Exception as e:
            logger.error(f"Error generating multiple variants: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def improve_post(self, channel_id: int, post_content: str, feedback: str) -> Dict:
        """Улучшение поста на основе обратной связи"""
        try:
            style_info = self.db.get_style_analysis(channel_id)
            
            if not style_info or not style_info['style_analysis']:
                return {
                    'success': False,
                    'error': 'Анализ стиля канала не найден'
                }
            
            improved_post = self.gemini.improve_post(
                post_content=post_content,
                style_analysis=style_info['style_analysis'],
                feedback=feedback
            )
            
            if not improved_post:
                return {
                    'success': False,
                    'error': 'Ошибка при улучшении поста'
                }
            
            return {
                'success': True,
                'improved_post': improved_post,
                'original_post': post_content,
                'feedback': feedback
            }
            
        except Exception as e:
            logger.error(f"Error improving post: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_channel_style_summary(self, channel_id: int) -> Dict:
        """Получение краткого описания стиля канала"""
        try:
            style_info = self.db.get_style_analysis(channel_id)
            
            if not style_info:
                return {
                    'success': False,
                    'error': 'Анализ стиля не найден'
                }
            
            # Получаем информацию о канале
            channels = self.db.get_user_channels(0)  # Нужно исправить для конкретного пользователя
            channel_info = None
            
            for channel in channels:
                if channel['channel_id'] == channel_id:
                    channel_info = channel
                    break
            
            return {
                'success': True,
                'channel_info': channel_info,
                'style_analysis': style_info['style_analysis'],
                'posts_count': style_info['posts_count'],
                'last_analysis': style_info['last_analysis']
            }
            
        except Exception as e:
            logger.error(f"Error getting channel style summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }
