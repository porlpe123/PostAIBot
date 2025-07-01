import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from telegram import Bot
from telegram.error import TelegramError
from database import Database
from gemini_client import GeminiClient
from config import MAX_POSTS_TO_ANALYZE, MIN_POSTS_FOR_ANALYSIS

logger = logging.getLogger(__name__)

class ChannelAnalyzer:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = Database()
        self.gemini = GeminiClient()
    
    async def analyze_channel(self, channel_id: int, user_id: int) -> Dict:
        """Полный анализ канала"""
        try:
            # Получаем информацию о канале
            chat = await self.bot.get_chat(channel_id)
            
            # Проверяем права бота
            bot_member = await self.bot.get_chat_member(channel_id, self.bot.id)
            if not bot_member.can_read_all_group_messages and chat.type != 'channel':
                return {
                    'success': False,
                    'error': 'Бот должен быть администратором с правами чтения сообщений'
                }
            
            # Добавляем канал в базу данных
            self.db.add_channel(
                channel_id=channel_id,
                channel_name=chat.title,
                channel_username=chat.username,
                user_id=user_id
            )
            
            # Получаем посты канала
            posts = await self._fetch_channel_posts(channel_id)
            
            if len(posts) < MIN_POSTS_FOR_ANALYSIS:
                return {
                    'success': False,
                    'error': f'Недостаточно постов для анализа. Минимум: {MIN_POSTS_FOR_ANALYSIS}, найдено: {len(posts)}'
                }
            
            # Сохраняем посты в базу данных
            self.db.add_posts(channel_id, posts)
            
            # Анализируем стиль
            style_analysis = self.gemini.analyze_channel_style(posts)
            
            if not style_analysis:
                return {
                    'success': False,
                    'error': 'Ошибка при анализе стиля канала'
                }
            
            # Сохраняем анализ
            self.db.save_style_analysis(channel_id, style_analysis, len(posts))
            
            return {
                'success': True,
                'channel_name': chat.title,
                'posts_analyzed': len(posts),
                'style_analysis': style_analysis
            }
            
        except TelegramError as e:
            logger.error(f"Telegram error analyzing channel {channel_id}: {e}")
            return {
                'success': False,
                'error': f'Ошибка Telegram: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error analyzing channel {channel_id}: {e}")
            return {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            }
    
    async def _fetch_channel_posts(self, channel_id: int) -> List[Dict]:
        """Получение постов из канала"""
        posts = []
        try:
            # Получаем последние сообщения
            messages = []
            offset = 0
            
            while len(messages) < MAX_POSTS_TO_ANALYZE:
                try:
                    # Получаем историю сообщений
                    updates = await self.bot.get_updates(
                        offset=offset,
                        limit=100,
                        timeout=10
                    )
                    
                    if not updates:
                        break
                    
                    for update in updates:
                        if (update.channel_post and 
                            update.channel_post.chat.id == channel_id and
                            update.channel_post.text):
                            
                            messages.append(update.channel_post)
                        
                        offset = update.update_id + 1
                    
                    if len(updates) < 100:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error fetching updates: {e}")
                    break
            
            # Альтернативный метод - через chat history (если доступен)
            if len(messages) < MIN_POSTS_FOR_ANALYSIS:
                messages = await self._fetch_chat_history(channel_id)
            
            # Обрабатываем сообщения
            for message in messages[:MAX_POSTS_TO_ANALYZE]:
                if message.text and len(message.text.strip()) > 10:
                    posts.append({
                        'post_id': message.message_id,
                        'content': message.text,
                        'date': message.date
                    })
            
            # Сортируем по дате (новые сначала)
            posts.sort(key=lambda x: x['date'], reverse=True)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching channel posts: {e}")
            return []
    
    async def _fetch_chat_history(self, channel_id: int) -> List:
        """Альтернативный метод получения истории чата"""
        try:
            # Этот метод может не работать для всех типов каналов
            # Здесь можно добавить дополнительную логику
            return []
        except Exception as e:
            logger.warning(f"Could not fetch chat history: {e}")
            return []
    
    async def update_channel_analysis(self, channel_id: int) -> Dict:
        """Обновление анализа канала"""
        try:
            # Получаем новые посты
            posts = await self._fetch_channel_posts(channel_id)
            
            if len(posts) < MIN_POSTS_FOR_ANALYSIS:
                return {
                    'success': False,
                    'error': 'Недостаточно постов для обновления анализа'
                }
            
            # Обновляем посты в базе данных
            self.db.add_posts(channel_id, posts)
            
            # Повторный анализ стиля
            style_analysis = self.gemini.analyze_channel_style(posts)
            
            if not style_analysis:
                return {
                    'success': False,
                    'error': 'Ошибка при обновлении анализа стиля'
                }
            
            # Сохраняем обновленный анализ
            self.db.save_style_analysis(channel_id, style_analysis, len(posts))
            
            return {
                'success': True,
                'posts_analyzed': len(posts),
                'updated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error updating channel analysis: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_channel_info(self, channel_id: int) -> Optional[Dict]:
        """Получение информации о канале"""
        try:
            # Получаем данные из базы
            channels = self.db.get_user_channels(0)  # Временно, нужно исправить
            for channel in channels:
                if channel['channel_id'] == channel_id:
                    # Получаем анализ стиля
                    style_info = self.db.get_style_analysis(channel_id)
                    channel.update(style_info or {})
                    return channel
            return None
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None
