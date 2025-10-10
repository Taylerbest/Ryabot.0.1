# interfaces/telegram_bot/handlers/__init__.py
"""
Handlers initialization - правильный порядок импортов
"""

import logging

# Импортируем роутеры в правильном порядке
from .start import router as start_router
from .tutorial import router as tutorial_router

# ВАЖНО: Специфичные роутеры ПЕРЕД общими
from .town_hall import router as town_hall_router
from .town import router as town_router

from .work import router as work_router
from .citizen import router as citizen_router
from .farm import router as farm_router
from .inventory import router as inventory_router
from .friends import router as friends_router
from .leaderboard import router as leaderboard_router
from .other import router as other_router
from .map import router as map_router
from .admin import router as admin_router
from .academy import router as academy_router
from .quantum_pass import router as quantum_pass_router
from .quantum_hub import router as quantum_hub_router
from .bank import router as bank_router
from .specialists import router as specialists_router

logger = logging.getLogger(__name__)

async def setup_handlers(dp):
    """Регистрация всех handlers в правильном порядке"""
    try:
        # Admin роутер первым (для доступа к админ командам)
        dp.include_router(admin_router)

        # Специфичные роутеры ПЕРЕД общими
        dp.include_router(town_hall_router)      # Ратуша
        dp.include_router(specialists_router)    # Специалисты
        dp.include_router(academy_router)        # Академия
        dp.include_router(bank_router)           # Банк
        dp.include_router(quantum_hub_router)     # Квантовый хаб
        dp.include_router(quantum_pass_router)    # Q-Pass

        # Общие роутеры
        dp.include_router(map_router)            # WebApp карта
        dp.include_router(tutorial_router)       # Обучение
        dp.include_router(citizen_router)        # Гражданин
        dp.include_router(town_router)           # Город (после town_hall!)
        dp.include_router(work_router)           # Работа
        dp.include_router(farm_router)           # Ферма
        dp.include_router(inventory_router)      # Инвентарь
        dp.include_router(friends_router)        # Друзья
        dp.include_router(leaderboard_router)    # Лидерборд
        dp.include_router(other_router)          # Прочее

        # Start handler последним (catch-all)
        dp.include_router(start_router)

        logger.info("✅ Все handlers успешно зарегистрированы")

    except Exception as e:
        logger.error(f"❌ Ошибка регистрации handlers: {e}")
        raise