#!/usr/bin/env python3
"""
PostAI Bot - Telegram бот для генерации постов в стиле канала
Использует Google Gemini API для анализа и генерации контента
"""

import asyncio
import logging
import sys
import signal
from bot import PostAIBot
from config import TELEGRAM_BOT_TOKEN, GEMINI_API_KEY

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        self.bot = None
        self.running = False
    
    async def start(self):
        """Запуск бота"""
        try:
            # Проверяем наличие необходимых токенов
            if not TELEGRAM_BOT_TOKEN:
                logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
                sys.exit(1)
            
            if not GEMINI_API_KEY:
                logger.error("GEMINI_API_KEY not found in environment variables")
                sys.exit(1)
            
            logger.info("Initializing PostAI Bot...")
            
            # Создаем экземпляр бота
            self.bot = PostAIBot()
            self.running = True
            
            # Настраиваем обработчики сигналов для graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            logger.info("Bot initialized successfully")
            logger.info("Starting bot polling...")
            
            # Запускаем бота
            await self.bot.start_bot()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            sys.exit(1)
        finally:
            await self.stop()
    
    async def stop(self):
        """Остановка бота"""
        if self.bot and self.running:
            logger.info("Shutting down bot...")
            self.running = False
            await self.bot.stop_bot()
            logger.info("Bot stopped successfully")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        logger.info(f"Received signal {signum}")
        self.running = False
        # Создаем задачу для остановки бота
        asyncio.create_task(self.stop())

async def main():
    """Главная функция"""
    logger.info("=" * 50)
    logger.info("PostAI Bot Starting...")
    logger.info("=" * 50)
    
    bot_manager = BotManager()
    
    try:
        await bot_manager.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
