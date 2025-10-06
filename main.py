# main.py
"""
Точка входа для Telegram бота Ryabot Island
"""

import asyncio
import logging
import sys
import os
import io
from pathlib import Path

# Добавляем родительскую директорию в Python path
sys.path.append(str(Path(__file__).parent))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import settings
from interfaces.telegram_bot.handlers import setup_handlers
from interfaces.telegram_bot.middlewares import setup_middlewares
from adapters.database.supabase.client import get_supabase_client, close_supabase_client

# Настройка логирования с поддержкой UTF-8 для Windows
console_handler = logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        console_handler
    ]
)

logger = logging.getLogger(__name__)

# Глобальные переменные
bot = None
dp = None


async def initialize_app():
    """Инициализация приложения"""
    global bot, dp

    logger.info("🚀 Запуск Ryabot Island Bot...")

    try:
        # Создаем директорию для логов
        Path('logs').mkdir(exist_ok=True)

        # Инициализация бота
        bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )

        # Инициализация dispatcher с memory storage
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        # ВАЖНО: Устанавливаем bot instance в blockchain_service
        from services.blockchain_service import blockchain_service
        blockchain_service.set_bot(bot)
        logger.info("✅ Bot instance установлен в blockchain_service")

        # Инициализация Supabase клиента
        supabase_client = await get_supabase_client()
        logger.info("✅ Подключение к Supabase установлено")

        # Регистрация handlers
        await setup_handlers(dp)
        logger.info("✅ Handlers зарегистрированы")

        # Регистрация middlewares
        await setup_middlewares(dp)

        # Инициализация game stats
        from config.game_stats import game_stats
        logger.info(f"✅ Game stats инициализированы (запуск: {game_stats.bot_start_time})")

        logger.info("🎉 Инициализация завершена успешно!")

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")
        raise


async def shutdown_app():
    """Завершение работы приложения"""
    global bot, dp

    logger.info("🛑 Остановка Ryabot Island Bot...")

    try:
        # Закрываем соединение с БД
        await close_supabase_client()
        logger.info("✅ Соединение с Supabase закрыто")

        # Закрываем сессию бота
        if bot:
            await bot.session.close()
            logger.info("✅ Сессия бота закрыта")

        logger.info("👋 Бот остановлен")

    except Exception as e:
        logger.error(f"❌ Ошибка при остановке: {e}")


async def main():
    """Главная функция"""
    try:
        # Инициализация
        await initialize_app()

        # Запуск polling
        logger.info("🔄 Запуск polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except KeyboardInterrupt:
        logger.info("⚠️ Получен сигнал остановки (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        # Завершение работы
        await shutdown_app()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Программа прервана пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")  # <-- ИСПРАВЛЕНО: убрана лишняя скобка
        sys.exit(1)
