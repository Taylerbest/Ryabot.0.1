import logging
from aiogram import Dispatcher

from .start import router as start_router
from .town import router as town_router  # ДОБАВИТЬ ЭТУ СТРОКУ

logger = logging.getLogger(__name__)


async def setup_handlers(dp: Dispatcher):
    """Регистрация всех handlers"""
    try:
        # Регистрируем роутеры
        dp.include_router(start_router)
        dp.include_router(town_router)  # ДОБАВИТЬ ЭТУ СТРОКУ

        logger.info("✅ Handlers зарегистрированы")

    except Exception as e:
        logger.error(f"❌ Ошибка регистрации handlers: {e}")
        raise