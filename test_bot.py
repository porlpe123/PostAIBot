#!/usr/bin/env python3
"""
Простые тесты для проверки основных компонентов PostAI Bot
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, AsyncMock

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestDatabase(unittest.TestCase):
    """Тесты для модуля базы данных"""
    
    def setUp(self):
        """Настройка тестовой базы данных"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Патчим путь к базе данных
        with patch('config.DATABASE_PATH', self.temp_db.name):
            from database import Database
            self.db = Database()
    
    def tearDown(self):
        """Очистка после тестов"""
        os.unlink(self.temp_db.name)
    
    def test_add_user(self):
        """Тест добавления пользователя"""
        result = self.db.add_user(
            user_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        self.assertTrue(result)
    
    def test_add_channel(self):
        """Тест добавления канала"""
        # Сначала добавляем пользователя
        self.db.add_user(12345, "testuser")
        
        # Добавляем канал
        result = self.db.add_channel(
            channel_id=-1001234567890,
            channel_name="Test Channel",
            user_id=12345,
            channel_username="testchannel"
        )
        self.assertTrue(result)
    
    def test_get_user_channels(self):
        """Тест получения каналов пользователя"""
        # Добавляем пользователя и канал
        self.db.add_user(12345, "testuser")
        self.db.add_channel(-1001234567890, "Test Channel", 12345)
        
        # Получаем каналы
        channels = self.db.get_user_channels(12345)
        self.assertEqual(len(channels), 1)
        self.assertEqual(channels[0]['channel_name'], "Test Channel")

class TestGeminiClient(unittest.TestCase):
    """Тесты для Gemini клиента"""
    
    def setUp(self):
        """Настройка мок-объектов"""
        self.mock_api_key = "test_api_key"
    
    @patch('config.GEMINI_API_KEY', 'test_api_key')
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_client_init(self, mock_model, mock_configure):
        """Тест инициализации Gemini клиента"""
        from gemini_client import GeminiClient
        
        client = GeminiClient()
        mock_configure.assert_called_once_with(api_key='test_api_key')
        mock_model.assert_called_once()
    
    @patch('config.GEMINI_API_KEY', 'test_api_key')
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_analyze_channel_style(self, mock_model_class, mock_configure):
        """Тест анализа стиля канала"""
        from gemini_client import GeminiClient
        
        # Настраиваем мок
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Анализ стиля канала"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        client = GeminiClient()
        
        # Тестовые посты
        posts = [
            {'content': 'Тестовый пост 1', 'date': '2024-01-01'},
            {'content': 'Тестовый пост 2', 'date': '2024-01-02'}
        ]
        
        result = client.analyze_channel_style(posts)
        self.assertEqual(result, "Анализ стиля канала")
        mock_model.generate_content.assert_called_once()

class TestPostGenerator(unittest.TestCase):
    """Тесты для генератора постов"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
    
    def tearDown(self):
        """Очистка после тестов"""
        os.unlink(self.temp_db.name)
    
    @patch('config.DATABASE_PATH')
    @patch('config.GEMINI_API_KEY', 'test_api_key')
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_generate_post_by_topic(self, mock_model_class, mock_configure, mock_db_path):
        """Тест генерации поста по теме"""
        mock_db_path.return_value = self.temp_db.name
        
        from post_generator import PostGenerator
        from database import Database
        
        # Настраиваем базу данных
        db = Database()
        db.save_style_analysis(
            channel_id=-1001234567890,
            style_analysis="Тестовый анализ стиля",
            posts_count=10
        )
        
        # Настраиваем мок Gemini
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Сгенерированный пост"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        generator = PostGenerator()
        result = generator.generate_post_by_topic(-1001234567890, "тестовая тема")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['post'], "Сгенерированный пост")
        self.assertEqual(result['topic'], "тестовая тема")

class TestConfig(unittest.TestCase):
    """Тесты для конфигурации"""
    
    def test_config_import(self):
        """Тест импорта конфигурации"""
        try:
            import config
            self.assertTrue(hasattr(config, 'WELCOME_MESSAGE'))
            self.assertTrue(hasattr(config, 'MAIN_MENU_KEYBOARD'))
            self.assertTrue(hasattr(config, 'MAX_POSTS_TO_ANALYZE'))
        except ImportError:
            self.fail("Не удалось импортировать модуль config")

def run_tests():
    """Запуск всех тестов"""
    print("🧪 Запуск тестов PostAI Bot...")
    print("=" * 40)
    
    # Создаем test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestGeminiClient))
    suite.addTests(loader.loadTestsFromTestCase(TestPostGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 40)
    if result.wasSuccessful():
        print("✅ Все тесты прошли успешно!")
        return True
    else:
        print("❌ Некоторые тесты не прошли")
        print(f"Ошибок: {len(result.errors)}")
        print(f"Неудач: {len(result.failures)}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
