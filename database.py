import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица пользователей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица каналов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS channels (
                        channel_id INTEGER PRIMARY KEY,
                        channel_name TEXT NOT NULL,
                        channel_username TEXT,
                        user_id INTEGER NOT NULL,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                # Таблица постов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        post_id INTEGER,
                        channel_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        post_date TIMESTAMP,
                        analyzed BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
                    )
                ''')
                
                # Таблица анализа стиля
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS channel_styles (
                        channel_id INTEGER PRIMARY KEY,
                        style_analysis TEXT,
                        posts_count INTEGER DEFAULT 0,
                        last_analysis TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """Добавление пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def add_channel(self, channel_id: int, channel_name: str, user_id: int, channel_username: str = None) -> bool:
        """Добавление канала"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO channels (channel_id, channel_name, channel_username, user_id)
                    VALUES (?, ?, ?, ?)
                ''', (channel_id, channel_name, channel_username, user_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding channel: {e}")
            return False
    
    def get_user_channels(self, user_id: int) -> List[Dict]:
        """Получение каналов пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT channel_id, channel_name, channel_username, added_at, is_active
                    FROM channels 
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY added_at DESC
                ''', (user_id,))
                
                channels = []
                for row in cursor.fetchall():
                    channels.append({
                        'channel_id': row[0],
                        'channel_name': row[1],
                        'channel_username': row[2],
                        'added_at': row[3],
                        'is_active': row[4]
                    })
                return channels
        except Exception as e:
            logger.error(f"Error getting user channels: {e}")
            return []
    
    def add_posts(self, channel_id: int, posts: List[Dict]) -> bool:
        """Добавление постов канала"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for post in posts:
                    cursor.execute('''
                        INSERT OR REPLACE INTO posts (post_id, channel_id, content, post_date)
                        VALUES (?, ?, ?, ?)
                    ''', (post['post_id'], channel_id, post['content'], post['date']))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding posts: {e}")
            return False
    
    def get_channel_posts(self, channel_id: int, limit: int = 50) -> List[Dict]:
        """Получение постов канала"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT content, post_date FROM posts 
                    WHERE channel_id = ? 
                    ORDER BY post_date DESC 
                    LIMIT ?
                ''', (channel_id, limit))
                
                posts = []
                for row in cursor.fetchall():
                    posts.append({
                        'content': row[0],
                        'date': row[1]
                    })
                return posts
        except Exception as e:
            logger.error(f"Error getting channel posts: {e}")
            return []
    
    def save_style_analysis(self, channel_id: int, style_analysis: str, posts_count: int) -> bool:
        """Сохранение анализа стиля канала"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO channel_styles (channel_id, style_analysis, posts_count, last_analysis)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (channel_id, style_analysis, posts_count))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving style analysis: {e}")
            return False
    
    def get_style_analysis(self, channel_id: int) -> Optional[Dict]:
        """Получение анализа стиля канала"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT style_analysis, posts_count, last_analysis 
                    FROM channel_styles 
                    WHERE channel_id = ?
                ''', (channel_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'style_analysis': row[0],
                        'posts_count': row[1],
                        'last_analysis': row[2]
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting style analysis: {e}")
            return None
