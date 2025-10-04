# interfaces/telegram_bot/middlewares/__init__.py
"""
Настройка middleware для Telegram Bot
"""

import logging
from aiogram import Dispatcher

logger = logging.getLogger(__name__)


async def setup_middlewares(dp: Dispatcher):
    """Настройка всех middleware"""
    try:
        # Пока что оставляем пустым
        # В будущем добавим:
        # - UserMiddleware (для автоматического получения пользователя)
        # - EnergyMiddleware (для проверки энергии)
        # - ThrottleMiddleware (для защиты от спама)
        # - LoggingMiddleware (для логирования действий)

        logger.info("✅ Middleware настроены")

    except Exception as e:
        logger.error(f"❌ Ошибка настройки middleware: {e}")
        raise
