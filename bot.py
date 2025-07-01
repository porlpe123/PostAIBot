import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)
from database import Database
from channel_analyzer import ChannelAnalyzer
from post_generator import PostGenerator
from config import (
    TELEGRAM_BOT_TOKEN, WELCOME_MESSAGE, HELP_MESSAGE,
    MAIN_MENU_KEYBOARD, CHANNELS_MENU_KEYBOARD, GENERATE_MENU_KEYBOARD
)

# Состояния для ConversationHandler
WAITING_CHANNEL_ID, WAITING_TOPIC, WAITING_FREE_TOPIC, WAITING_FEEDBACK = range(4)

logger = logging.getLogger(__name__)

class PostAIBot:
    def __init__(self):
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.db = Database()
        self.channel_analyzer = None  # Будет инициализирован в start_bot
        self.post_generator = PostGenerator()
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        
        # Основные команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("channels", self.channels_command))
        self.application.add_handler(CommandHandler("generate", self.generate_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        
        # ConversationHandler для добавления канала
        add_channel_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.add_channel_start, pattern="^add_channel$")],
            states={
                WAITING_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_channel_process)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_operation)]
        )
        self.application.add_handler(add_channel_conv)
        
        # ConversationHandler для генерации по теме
        topic_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.topic_generation_start, pattern="^generate_topic_")],
            states={
                WAITING_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.generate_by_topic)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_operation)]
        )
        self.application.add_handler(topic_conv)
        
        # ConversationHandler для свободной темы
        free_topic_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.free_topic_start, pattern="^generate_free_")],
            states={
                WAITING_FREE_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.generate_free_topic)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_operation)]
        )
        self.application.add_handler(free_topic_conv)
        
        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Обработчик текстовых сообщений (кнопки меню)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_menu))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Добавляем пользователя в базу данных
        self.db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Инициализируем анализатор каналов
        if not self.channel_analyzer:
            self.channel_analyzer = ChannelAnalyzer(context.bot)
        
        keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
        
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        await update.message.reply_text(HELP_MESSAGE, parse_mode='HTML')
    
    async def channels_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /channels"""
        keyboard = ReplyKeyboardMarkup(CHANNELS_MENU_KEYBOARD, resize_keyboard=True)
        await update.message.reply_text(
            "🔧 Управление каналами\n\nВыберите действие:",
            reply_markup=keyboard
        )
    
    async def generate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /generate"""
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        if not channels:
            await update.message.reply_text(
                "❌ У вас нет добавленных каналов.\n"
                "Сначала добавьте канал через меню 'Мои каналы'."
            )
            return
        
        keyboard = ReplyKeyboardMarkup(GENERATE_MENU_KEYBOARD, resize_keyboard=True)
        await update.message.reply_text(
            "✨ Генерация постов\n\nВыберите тип генерации:",
            reply_markup=keyboard
        )
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /settings"""
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        settings_text = f"""
⚙️ Настройки бота

👤 Пользователь: {update.effective_user.first_name}
📊 Каналов добавлено: {len(channels)}
🤖 Модель ИИ: Gemini 2.0 Flash

📋 Ваши каналы:
"""
        
        for i, channel in enumerate(channels, 1):
            settings_text += f"{i}. {channel['channel_name']}\n"
        
        if not channels:
            settings_text += "Нет добавленных каналов"
        
        await update.message.reply_text(settings_text)
    
    async def handle_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик кнопок главного меню"""
        text = update.message.text
        user_id = update.effective_user.id
        
        if text == "📊 Мои каналы":
            await self.show_channels_menu(update, context)
        
        elif text == "✨ Генерировать пост":
            await self.show_generate_menu(update, context)
        
        elif text == "⚙️ Настройки":
            await self.settings_command(update, context)
        
        elif text == "❓ Помощь":
            await self.help_command(update, context)
        
        elif text == "➕ Добавить канал":
            await self.show_add_channel_instructions(update, context)
        
        elif text == "📋 Список каналов":
            await self.show_channels_list(update, context)
        
        elif text == "🔄 Обновить анализ":
            await self.show_update_analysis_menu(update, context)
        
        elif text == "🏠 Главное меню":
            keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
            await update.message.reply_text(
                "🏠 Главное меню",
                reply_markup=keyboard
            )
        
        elif text in ["🎯 По теме", "🎲 Случайный пост", "📝 Свободная тема"]:
            await self.handle_generation_type(update, context, text)
    
    async def show_channels_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню управления каналами"""
        keyboard = ReplyKeyboardMarkup(CHANNELS_MENU_KEYBOARD, resize_keyboard=True)
        await update.message.reply_text(
            "📊 Управление каналами\n\nВыберите действие:",
            reply_markup=keyboard
        )
    
    async def show_generate_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню генерации"""
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)
        
        if not channels:
            await update.message.reply_text(
                "❌ У вас нет добавленных каналов.\n"
                "Сначала добавьте канал через меню 'Мои каналы'."
            )
            return
        
        keyboard = ReplyKeyboardMarkup(GENERATE_MENU_KEYBOARD, resize_keyboard=True)
        await update.message.reply_text(
            "✨ Генерация постов\n\nВыберите тип генерации:",
            reply_markup=keyboard
        )
    
    async def show_add_channel_instructions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать инструкции по добавлению канала"""
        instructions = """
📝 Как добавить канал:

1️⃣ Добавьте этого бота в ваш Telegram канал как администратора
2️⃣ Дайте боту права на чтение сообщений
3️⃣ Отправьте ID канала или перешлите любое сообщение из канала

💡 Чтобы узнать ID канала:
• Перешлите сообщение из канала боту @userinfobot
• Или используйте @getidsbot

Отправьте ID канала (например: -1001234567890):
"""
        
        await update.message.reply_text(instructions)
        return WAITING_CHANNEL_ID

    async def show_channels_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список каналов пользователя"""
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)

        if not channels:
            await update.message.reply_text(
                "📋 У вас нет добавленных каналов.\n"
                "Используйте кнопку '➕ Добавить канал' для добавления."
            )
            return

        channels_text = "📋 Ваши каналы:\n\n"

        for i, channel in enumerate(channels, 1):
            # Получаем информацию об анализе
            style_info = self.db.get_style_analysis(channel['channel_id'])
            status = "✅ Проанализирован" if style_info else "⏳ Требует анализа"

            channels_text += f"{i}. **{channel['channel_name']}**\n"
            channels_text += f"   ID: `{channel['channel_id']}`\n"
            channels_text += f"   Статус: {status}\n"
            if style_info:
                channels_text += f"   Постов: {style_info['posts_count']}\n"
            channels_text += f"   Добавлен: {channel['added_at'][:10]}\n\n"

        # Создаем inline клавиатуру для действий с каналами
        keyboard = []
        for channel in channels:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔄 {channel['channel_name'][:20]}...",
                    callback_data=f"update_analysis_{channel['channel_id']}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            channels_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_update_analysis_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню обновления анализа"""
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)

        if not channels:
            await update.message.reply_text(
                "❌ У вас нет добавленных каналов для обновления анализа."
            )
            return

        keyboard = []
        for channel in channels:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔄 {channel['channel_name']}",
                    callback_data=f"update_analysis_{channel['channel_id']}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🔄 Выберите канал для обновления анализа:",
            reply_markup=reply_markup
        )

    async def handle_generation_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE, generation_type: str):
        """Обработка типа генерации"""
        user_id = update.effective_user.id
        channels = self.db.get_user_channels(user_id)

        if not channels:
            await update.message.reply_text(
                "❌ У вас нет добавленных каналов."
            )
            return

        # Создаем клавиатуру с каналами
        keyboard = []
        for channel in channels:
            style_info = self.db.get_style_analysis(channel['channel_id'])
            if style_info:  # Только каналы с анализом
                if generation_type == "🎯 По теме":
                    callback_data = f"generate_topic_{channel['channel_id']}"
                elif generation_type == "🎲 Случайный пост":
                    callback_data = f"generate_random_{channel['channel_id']}"
                elif generation_type == "📝 Свободная тема":
                    callback_data = f"generate_free_{channel['channel_id']}"

                keyboard.append([
                    InlineKeyboardButton(
                        channel['channel_name'],
                        callback_data=callback_data
                    )
                ])

        if not keyboard:
            await update.message.reply_text(
                "❌ Нет каналов с завершенным анализом.\n"
                "Сначала проанализируйте ваши каналы."
            )
            return

        reply_markup = InlineKeyboardMarkup(keyboard)

        type_text = {
            "🎯 По теме": "Выберите канал для генерации поста по теме:",
            "🎲 Случайный пост": "Выберите канал для генерации случайного поста:",
            "📝 Свободная тема": "Выберите канал для генерации поста на свободную тему:"
        }

        await update.message.reply_text(
            type_text[generation_type],
            reply_markup=reply_markup
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data.startswith("update_analysis_"):
            channel_id = int(data.split("_")[2])
            await self.update_channel_analysis(query, context, channel_id)

        elif data.startswith("generate_random_"):
            channel_id = int(data.split("_")[2])
            await self.generate_random_post(query, context, channel_id)

        elif data.startswith("generate_topic_"):
            channel_id = int(data.split("_")[2])
            context.user_data['selected_channel'] = channel_id
            await query.edit_message_text(
                "🎯 Введите тему для поста:\n\n"
                "Например: 'новости технологий', 'мотивация', 'обзор продукта'"
            )
            return WAITING_TOPIC

        elif data.startswith("generate_free_"):
            channel_id = int(data.split("_")[2])
            context.user_data['selected_channel'] = channel_id
            await query.edit_message_text(
                "📝 Опишите, о чем должен быть пост:\n\n"
                "Будьте максимально подробными в описании желаемого контента."
            )
            return WAITING_FREE_TOPIC

    async def add_channel_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало процесса добавления канала"""
        query = update.callback_query
        await query.answer()

        instructions = """
📝 Добавление канала:

1️⃣ Добавьте бота в канал как администратора
2️⃣ Дайте права на чтение сообщений
3️⃣ Отправьте ID канала (например: -1001234567890)

💡 Для получения ID канала используйте @userinfobot

Отправьте ID канала:
"""
        await query.edit_message_text(instructions)
        return WAITING_CHANNEL_ID

    async def add_channel_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка добавления канала"""
        user_id = update.effective_user.id
        channel_input = update.message.text.strip()

        # Проверяем формат ID канала
        try:
            if channel_input.startswith('-100'):
                channel_id = int(channel_input)
            elif channel_input.startswith('@'):
                # Обработка username канала
                await update.message.reply_text(
                    "❌ Пожалуйста, используйте числовой ID канала, а не username."
                )
                return WAITING_CHANNEL_ID
            else:
                channel_id = int(channel_input)
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат ID канала. Попробуйте еще раз:"
            )
            return WAITING_CHANNEL_ID

        # Показываем сообщение о начале анализа
        analyzing_msg = await update.message.reply_text(
            "🔄 Анализирую канал...\n"
            "Это может занять несколько минут."
        )

        # Анализируем канал
        if not self.channel_analyzer:
            self.channel_analyzer = ChannelAnalyzer(context.bot)

        result = await self.channel_analyzer.analyze_channel(channel_id, user_id)

        await analyzing_msg.delete()

        if result['success']:
            success_text = f"""
✅ Канал успешно добавлен и проанализирован!

📊 **{result['channel_name']}**
📈 Проанализировано постов: {result['posts_analyzed']}

Теперь вы можете генерировать посты в стиле этого канала!
"""
            keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
            await update.message.reply_text(
                success_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ Ошибка при добавлении канала:\n{result['error']}\n\n"
                "Попробуйте еще раз или обратитесь к инструкции."
            )
            return WAITING_CHANNEL_ID

        return ConversationHandler.END

    async def topic_generation_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало генерации по теме"""
        # Этот метод вызывается через callback, логика уже в handle_callback
        pass

    async def generate_by_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Генерация поста по теме"""
        topic = update.message.text.strip()
        channel_id = context.user_data.get('selected_channel')

        if not channel_id:
            await update.message.reply_text("❌ Ошибка: канал не выбран.")
            return ConversationHandler.END

        # Показываем сообщение о генерации
        generating_msg = await update.message.reply_text(
            "✨ Генерирую пост по теме...\n"
            "Пожалуйста, подождите."
        )

        # Генерируем пост
        result = self.post_generator.generate_post_by_topic(channel_id, topic)

        await generating_msg.delete()

        if result['success']:
            post_text = f"""
✨ **Сгенерированный пост:**

{result['post']}

---
🎯 Тема: {result['topic']}
"""
            # Создаем клавиатуру для действий с постом
            keyboard = [
                [InlineKeyboardButton("🔄 Сгенерировать еще", callback_data=f"generate_topic_{channel_id}")],
                [InlineKeyboardButton("📝 Улучшить пост", callback_data=f"improve_post_{channel_id}")],
                [InlineKeyboardButton("📋 Копировать", callback_data="copy_post")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                post_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ Ошибка при генерации поста:\n{result['error']}"
            )

        return ConversationHandler.END

    async def free_topic_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало генерации свободной темы"""
        # Логика уже в handle_callback
        pass

    async def generate_free_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Генерация поста на свободную тему"""
        user_request = update.message.text.strip()
        channel_id = context.user_data.get('selected_channel')

        if not channel_id:
            await update.message.reply_text("❌ Ошибка: канал не выбран.")
            return ConversationHandler.END

        generating_msg = await update.message.reply_text(
            "✨ Генерирую пост...\n"
            "Пожалуйста, подождите."
        )

        result = self.post_generator.generate_free_topic_post(channel_id, user_request)

        await generating_msg.delete()

        if result['success']:
            post_text = f"""
✨ **Сгенерированный пост:**

{result['post']}

---
📝 Запрос: {result['topic']}
"""
            keyboard = [
                [InlineKeyboardButton("🔄 Сгенерировать еще", callback_data=f"generate_free_{channel_id}")],
                [InlineKeyboardButton("📝 Улучшить пост", callback_data=f"improve_post_{channel_id}")],
                [InlineKeyboardButton("📋 Копировать", callback_data="copy_post")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                post_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ Ошибка при генерации поста:\n{result['error']}"
            )

        return ConversationHandler.END

    async def generate_random_post(self, query, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
        """Генерация случайного поста"""
        await query.edit_message_text(
            "✨ Генерирую случайный пост...\n"
            "Пожалуйста, подождите."
        )

        result = self.post_generator.generate_random_post(channel_id)

        if result['success']:
            post_text = f"""
✨ **Случайный пост:**

{result['post']}

---
🎲 Тема: {result['topic']}
"""
            keyboard = [
                [InlineKeyboardButton("🔄 Еще случайный", callback_data=f"generate_random_{channel_id}")],
                [InlineKeyboardButton("📝 Улучшить пост", callback_data=f"improve_post_{channel_id}")],
                [InlineKeyboardButton("📋 Копировать", callback_data="copy_post")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                post_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"❌ Ошибка при генерации поста:\n{result['error']}"
            )

    async def update_channel_analysis(self, query, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
        """Обновление анализа канала"""
        await query.edit_message_text(
            "🔄 Обновляю анализ канала...\n"
            "Это может занять несколько минут."
        )

        if not self.channel_analyzer:
            self.channel_analyzer = ChannelAnalyzer(context.bot)

        result = await self.channel_analyzer.update_channel_analysis(channel_id)

        if result['success']:
            await query.edit_message_text(
                f"✅ Анализ канала обновлен!\n\n"
                f"📈 Проанализировано постов: {result['posts_analyzed']}\n"
                f"🕐 Обновлено: {result['updated_at'].strftime('%d.%m.%Y %H:%M')}"
            )
        else:
            await query.edit_message_text(
                f"❌ Ошибка при обновлении анализа:\n{result['error']}"
            )

    async def cancel_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена текущей операции"""
        keyboard = ReplyKeyboardMarkup(MAIN_MENU_KEYBOARD, resize_keyboard=True)
        await update.message.reply_text(
            "❌ Операция отменена.",
            reply_markup=keyboard
        )
        return ConversationHandler.END

    async def start_bot(self):
        """Запуск бота"""
        logger.info("Starting PostAI Bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

        logger.info("Bot is running...")

        # Ожидаем завершения
        await self.application.updater.idle()

    async def stop_bot(self):
        """Остановка бота"""
        logger.info("Stopping PostAI Bot...")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
