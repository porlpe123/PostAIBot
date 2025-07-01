#!/usr/bin/env python3
"""
Альтернативный скрипт запуска PostAI Bot
Исправляет проблемы совместимости с python-telegram-bot
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

class BotRunner:
    def __init__(self):
        self.bot = None
        self.running = False
    
    async def start(self):
        """Запуск бота с улучшенной обработкой ошибок"""
        try:
            # Проверяем наличие необходимых токенов
            if not TELEGRAM_BOT_TOKEN:
                logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
                logger.error("Please create .env file with your bot token")
                sys.exit(1)
            
            if not GEMINI_API_KEY:
                logger.error("GEMINI_API_KEY not found in environment variables")
                logger.error("Please add your Gemini API key to .env file")
                sys.exit(1)
            
            logger.info("=" * 60)
            logger.info("PostAI Bot v2.0 Starting...")
            logger.info("=" * 60)
            
            # Создаем экземпляр бота
            self.bot = PostAIBot()
            self.running = True
            
            logger.info("Bot initialized successfully")
            logger.info("Starting Telegram polling...")
            
            # Запускаем бота
            await self.bot.application.initialize()
            await self.bot.application.start()
            await self.bot.application.updater.start_polling()
            
            logger.info("🤖 Bot is running successfully!")
            logger.info("📱 You can now interact with your bot in Telegram")
            logger.info("⏹️  Press Ctrl+C to stop the bot")
            logger.info("-" * 60)
            
            # Ожидаем завершения
            try:
                # Пробуем использовать idle() если доступен
                await self.bot.application.updater.idle()
            except AttributeError:
                # Fallback для новых версий
                logger.info("Using fallback event loop for compatibility")
                try:
                    while self.running:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Received keyboard interrupt")
                    self.running = False
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.running = False
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            logger.error("Check your .env file and internet connection")
            sys.exit(1)
        finally:
            await self.stop()
    
    async def stop(self):
        """Остановка бота"""
        if self.bot and self.running:
            logger.info("Shutting down bot...")
            self.running = False
            try:
                await self.bot.application.updater.stop()
                await self.bot.application.stop()
                await self.bot.application.shutdown()
                logger.info("✅ Bot stopped successfully")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        logger.info(f"Received signal {signum}")
        self.running = False

async def main():
    """Главная функция"""
    bot_runner = BotRunner()
    
    # Настраиваем обработчики сигналов
    signal.signal(signal.SIGINT, bot_runner._signal_handler)
    signal.signal(signal.SIGTERM, bot_runner._signal_handler)
    
    try:
        await bot_runner.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
