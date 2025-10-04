# interfaces/telegram_bot/handlers/__init__.py
"""
Настройка всех handlers для Telegram Bot
"""

import logging
from aiogram import Dispatcher

from .start import router as start_router

logger = logging.getLogger(__name__)


async def setup_handlers(dp: Dispatcher):
    """Регистрация всех handlers"""
    try:
        # Регистрируем роутеры
        dp.include_router(start_router)

        logger.info("✅ Handlers зарегистрированы")

        # В будущем добавить:
        # dp.include_router(academy_router)
        # dp.include_router(farm_router)
        # dp.include_router(town_router)
        # dp.include_router(work_router)
        # dp.include_router(character_router)
        # dp.include_router(admin_router)

    except Exception as e:
        logger.error(f"❌ Ошибка регистрации handlers: {e}")
        raise