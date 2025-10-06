# interfaces/telegram_bot/middlewares/__init__.py
"""
Настройка middleware для Telegram Bot
"""

import logging
from aiogram import Dispatcher
from .energy_middleware import EnergyMiddleware

logger = logging.getLogger(__name__)


async def setup_middlewares(dp: Dispatcher):
    """Настройка всех middleware"""
    try:
        # Energy Middleware для автоматической регенерации энергии
        energy_middleware = EnergyMiddleware()
        dp.message.middleware(energy_middleware)
        dp.callback_query.middleware(energy_middleware)

        logger.info("✅ Energy middleware зарегистрирован")

        # В будущем добавим:
        # - UserMiddleware (для автоматического получения пользователя)
        # - ThrottleMiddleware (для защиты от спама)
        # - LoggingMiddleware (для логирования действий)

        logger.info("✅ Все middleware настроены")

    except Exception as e:
        logger.error(f"❌ Ошибка настройки middleware: {e}")
        raise
