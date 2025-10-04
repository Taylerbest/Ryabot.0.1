# main.py
"""
Главный файл приложения Ryabot Island
Точка входа в приложение
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Добавляем корневую папку в Python path
sys.path.append(str(Path(__file__).parent))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import settings
from interfaces.telegram_bot.handlers import setup_handlers
from interfaces.telegram_bot.middlewares import setup_middlewares
from adapters.database.supabase.client import get_supabase_client, close_supabase_client

# Глобальные объекты
bot: Bot = None
dp: Dispatcher = None

async def initialize_app():
    """Инициализация приложения"""
    global bot, dp
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Запуск Ryabot Island Bot...")
    
    try:
        # 1. Создаем папки для логов если их нет
        os.makedirs("logs", exist_ok=True)
        
        # 2. Инициализируем Telegram Bot
        bot = Bot(token=settings.BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # 3. Инициализируем базу данных
        logger.info(f"📊 Инициализация БД: {settings.DATABASE_TYPE.value}")
        supabase_client = await get_supabase_client()
        logger.info("✅ База данных подключена")
        
        # 4. Настраиваем middleware
        await setup_middlewares(dp)
        
        # 5. Настраиваем handlers
        await setup_handlers(dp)
        
        # 6. Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот @{bot_info.username} готов к работе")
        logger.info(f"📱 Режим: {'🔧 Разработка' if settings.DEBUG else '🚀 Продакшен'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации приложения: {e}")
        return False

async def shutdown_app():
    """Корректное завершение приложения"""
    logger = logging.getLogger(__name__)
    logger.info("🛑 Завершение работы бота...")
    
    try:
        # Закрываем соединения
        if bot:
            await bot.session.close()
            logger.info("✅ Telegram Bot отключен")
        
        await close_supabase_client()
        logger.info("✅ База данных отключена")
        
        logger.info("✅ Приложение корректно завершено")
        
    except Exception as e:
        logger.error(f"❌ Ошибка завершения приложения: {e}")

async def main():
    """Главная функция"""
    try:
        # Инициализируем приложение
        if not await initialize_app():
            print("❌ Не удалось инициализировать приложение")
            return 1
        
        # Запускаем polling
        print("🎮 Ryabot Island Bot запущен!")
        print(f"💬 Отправьте /start боту @{settings.BOT_USERNAME}")
        print("🔄 Нажмите Ctrl+C для остановки\n")
        
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        print("\n⏹️ Получен сигнал остановки")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return 1
    finally:
        await shutdown_app()
    
    return 0

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Отключаем лишние логи aiogram
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("aiogram.dispatcher").setLevel(logging.WARNING)
    
    # Запускаем
    exit_code = asyncio.run(main())