import logging
from aiogram import Dispatcher

from .start import router as start_router
from .town import router as town_router
from .tutorial import router as tutorial_router
from .work import router as work_router  # ДОБАВИТЬ

logger = logging.getLogger(__name__)


async def setup_handlers(dp: Dispatcher):
    """Регистрация всех handlers"""
    try:
        dp.include_router(tutorial_router)  # Сначала туториал
        dp.include_router(work_router)  # Затем работы
        dp.include_router(town_router)  # Затем город
        dp.include_router(start_router)  # Последним общие команды

        logger.info("✅ Handlers зарегистрированы")

    except Exception as e:
        logger.error(f"❌ Ошибка регистрации handlers: {e}")
        raise