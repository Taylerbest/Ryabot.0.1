# interfaces/telegram_bot/handlers/__init__.py
"""
Регистрация всех handlers
"""

import logging
from aiogram import Dispatcher

# Импортируем все routers
from .start import router as start_router
from .tutorial import router as tutorial_router
from .town import router as town_router
from .work import router as work_router
from .citizen import router as citizen_router
from .farm import router as farm_router
from .inventory import router as inventory_router
from .friends import router as friends_router
from .leaderboard import router as leaderboard_router
from .other import router as other_router

logger = logging.getLogger(__name__)


async def setup_handlers(dp: Dispatcher):
    """Регистрация всех handlers"""
    try:
        # ВАЖНО: Порядок регистрации имеет значение!
        # Специфичные handlers должны быть ВЫШЕ более общих

        dp.include_router(tutorial_router)  # Туториал (специфичный)
        dp.include_router(citizen_router)  # Житель
        dp.include_router(town_router)  # Город
        dp.include_router(work_router)  # Работы
        dp.include_router(farm_router)  # Ферма
        dp.include_router(inventory_router)  # Рюкзак
        dp.include_router(friends_router)  # Друзья
        dp.include_router(leaderboard_router)  # Лидерборд
        dp.include_router(other_router)  # Прочее
        dp.include_router(start_router)  # Основной handler (ПОСЛЕДНИМ!)

        logger.info("✅ Все handlers зарегистрированы успешно")

    except Exception as e:
        logger.error(f"❌ Ошибка регистрации handlers: {e}")
        raise
