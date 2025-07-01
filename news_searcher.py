import asyncio
import aiohttp
import feedparser
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
# from newspaper import Article  # Временно отключено из-за проблем с lxml.html.clean
from config import RSS_SOURCES, MAX_NEWS_ARTICLES, NEWS_SEARCH_TIMEOUT, ENABLE_NEWS_SEARCH

logger = logging.getLogger(__name__)

class NewsSearcher:
    def __init__(self):
        self.session = None
        self.rss_sources = RSS_SOURCES
        self.max_articles = MAX_NEWS_ARTICLES
        self.timeout = NEWS_SEARCH_TIMEOUT
        self.enabled = ENABLE_NEWS_SEARCH
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search_news_by_topic(self, topic: str, max_results: int = None) -> List[Dict]:
        """Поиск новостей по теме"""
        if not self.enabled:
            logger.info("News search is disabled")
            return []
        
        max_results = max_results or self.max_articles
        logger.info(f"Searching news for topic: {topic}")
        
        try:
            # Комбинируем результаты из разных источников
            all_articles = []
            
            # 1. Поиск в RSS лентах
            rss_articles = await self._search_rss_feeds(topic, max_results // 2)
            all_articles.extend(rss_articles)
            
            # 2. Поиск через Google News (если доступен)
            google_articles = await self._search_google_news(topic, max_results // 2)
            all_articles.extend(google_articles)
            
            # 3. Поиск в Яндекс.Новостях
            yandex_articles = await self._search_yandex_news(topic, max_results // 2)
            all_articles.extend(yandex_articles)
            
            # Удаляем дубликаты и сортируем по дате
            unique_articles = self._remove_duplicates(all_articles)
            sorted_articles = sorted(
                unique_articles, 
                key=lambda x: x.get('published', datetime.min), 
                reverse=True
            )
            
            return sorted_articles[:max_results]
            
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            return []
    
    async def get_latest_news(self, max_results: int = None) -> List[Dict]:
        """Получение последних новостей"""
        max_results = max_results or self.max_articles
        logger.info("Fetching latest news")
        
        try:
            all_articles = []
            
            # Получаем новости из RSS лент
            for source in self.rss_sources:
                try:
                    articles = await self._fetch_rss_feed(source, max_results // len(self.rss_sources))
                    all_articles.extend(articles)
                except Exception as e:
                    logger.warning(f"Error fetching from {source}: {e}")
                    continue
            
            # Сортируем по дате и возвращаем топ
            sorted_articles = sorted(
                all_articles,
                key=lambda x: x.get('published', datetime.min),
                reverse=True
            )
            
            return sorted_articles[:max_results]
            
        except Exception as e:
            logger.error(f"Error getting latest news: {e}")
            return []
    
    async def _search_rss_feeds(self, topic: str, max_results: int) -> List[Dict]:
        """Поиск в RSS лентах"""
        articles = []
        topic_lower = topic.lower()
        
        for source in self.rss_sources:
            try:
                feed_articles = await self._fetch_rss_feed(source)
                
                # Фильтруем по теме
                for article in feed_articles:
                    title = article.get('title', '').lower()
                    summary = article.get('summary', '').lower()
                    
                    if topic_lower in title or topic_lower in summary:
                        articles.append(article)
                        
                        if len(articles) >= max_results:
                            break
                
                if len(articles) >= max_results:
                    break
                    
            except Exception as e:
                logger.warning(f"Error searching RSS feed {source}: {e}")
                continue
        
        return articles
    
    async def _fetch_rss_feed(self, url: str, max_articles: int = 20) -> List[Dict]:
        """Получение статей из RSS ленты"""
        try:
            if self.session:
                async with self.session.get(url) as response:
                    content = await response.text()
            else:
                # Fallback для синхронного запроса
                response = requests.get(url, timeout=self.timeout)
                content = response.text
            
            feed = feedparser.parse(content)
            articles = []
            
            for entry in feed.entries[:max_articles]:
                article = {
                    'title': entry.get('title', 'No title'),
                    'summary': entry.get('summary', entry.get('description', '')),
                    'link': entry.get('link', ''),
                    'published': self._parse_date(entry.get('published')),
                    'source': feed.feed.get('title', url),
                    'type': 'rss'
                }
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
            return []
    
    async def _search_google_news(self, topic: str, max_results: int) -> List[Dict]:
        """Поиск в Google News (через RSS)"""
        try:
            # Google News RSS URL
            google_news_url = f"https://news.google.com/rss/search?q={topic}&hl=ru&gl=RU&ceid=RU:ru"
            
            return await self._fetch_rss_feed(google_news_url, max_results)
            
        except Exception as e:
            logger.error(f"Error searching Google News: {e}")
            return []
    
    async def _search_yandex_news(self, topic: str, max_results: int) -> List[Dict]:
        """Поиск в Яндекс.Новостях"""
        try:
            # Яндекс.Новости RSS (общая лента)
            yandex_url = "https://news.yandex.ru/index.rss"
            articles = await self._fetch_rss_feed(yandex_url, max_results * 2)
            
            # Фильтруем по теме
            topic_lower = topic.lower()
            filtered_articles = []
            
            for article in articles:
                title = article.get('title', '').lower()
                summary = article.get('summary', '').lower()
                
                if topic_lower in title or topic_lower in summary:
                    filtered_articles.append(article)
                    
                    if len(filtered_articles) >= max_results:
                        break
            
            return filtered_articles
            
        except Exception as e:
            logger.error(f"Error searching Yandex News: {e}")
            return []
    
    def _parse_date(self, date_str: str) -> datetime:
        """Парсинг даты из различных форматов"""
        if not date_str:
            return datetime.min
        
        try:
            # Пробуем различные форматы
            formats = [
                '%a, %d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S %Z',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S',
                '%d.%m.%Y %H:%M'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # Если ничего не подошло, возвращаем текущее время
            return datetime.now()
            
        except Exception:
            return datetime.min
    
    def _remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Удаление дубликатов статей"""
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            title = article.get('title', '').strip().lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
        
        return unique_articles
    
    async def get_article_content(self, url: str) -> Optional[str]:
        """Получение полного содержимого статьи (временно отключено)"""
        try:
            # Временно отключено из-за проблем с newspaper3k и lxml.html.clean
            # В будущих версиях будет заменено на альтернативное решение
            logger.warning("Article content extraction temporarily disabled due to lxml.html.clean compatibility issues")
            return None

            # Оригинальный код (закомментирован):
            # article = Article(url)
            # article.download()
            # article.parse()
            # return article.text

        except Exception as e:
            logger.error(f"Error getting article content from {url}: {e}")
            return None
    
    def format_news_summary(self, articles: List[Dict], max_articles: int = 5) -> str:
        """Форматирование новостей для отправки пользователю"""
        if not articles:
            return "📰 Новости не найдены"
        
        summary = "📰 **Последние новости:**\n\n"
        
        for i, article in enumerate(articles[:max_articles], 1):
            title = article.get('title', 'Без заголовка')
            source = article.get('source', 'Неизвестный источник')
            link = article.get('link', '')
            published = article.get('published')
            
            summary += f"**{i}. {title}**\n"
            summary += f"📅 {source}"
            
            if published and published != datetime.min:
                summary += f" • {published.strftime('%d.%m.%Y %H:%M')}"
            
            if link:
                summary += f"\n🔗 [Читать полностью]({link})"
            
            summary += "\n\n"
        
        return summary

# Функция для использования без async context manager
async def search_news(topic: str, max_results: int = 5) -> List[Dict]:
    """Простая функция поиска новостей"""
    async with NewsSearcher() as searcher:
        return await searcher.search_news_by_topic(topic, max_results)

async def get_latest_news(max_results: int = 5) -> List[Dict]:
    """Простая функция получения последних новостей"""
    async with NewsSearcher() as searcher:
        return await searcher.get_latest_news(max_results)
