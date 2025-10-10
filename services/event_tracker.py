# services/event_tracker.py
"""
Event Tracker Service - система трекинга событий
Упрощённая версия для работы с лицензиями
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Типы событий"""
    USER_LOGIN = "user_login"
    USER_REGISTER = "user_register"
    CURRENCY_SPENT = "currency_spent"
    CURRENCY_EARNED = "currency_earned"
    RBTC_TRANSACTION = "rbtc_transaction"
    LICENSE_UPGRADED = "license_upgraded"
    SPECIALIST_HIRED = "specialist_hired"
    ITEM_PURCHASED = "item_purchased"
    BUILDING_BUILT = "building_built"
    QUEST_COMPLETED = "quest_completed"
    EXPEDITION_COMPLETED = "expedition_completed"

class EventSignificance(Enum):
    """Уровни значимости событий"""
    LOW = 0
    NORMAL = 1
    IMPORTANT = 2
    CRITICAL = 3

class EventTracker:
    """Сервис трекинга событий"""

    def __init__(self, client=None):
        self.client = client
        logger.info("✅ EventTracker инициализирован")

    async def track_event(self, user_id: int, event_type: EventType,
                         data: Dict[str, Any], significance: EventSignificance = EventSignificance.NORMAL):
        """Трекинг общего события"""
        try:
            logger.info(f"📊 Event: {event_type.value} | User: {user_id} | Significance: {significance.value}")
            logger.debug(f"Event data: {data}")

            # TODO: сохранить в базу данных если нужно
            # if self.client:
            #     await self.client.execute_query(...)

            return True
        except Exception as e:
            logger.error(f"Ошибка трекинга события {event_type.value}: {e}")
            return False

    async def track_currency_spent(self, user_id: int, currency_type: str,
                                   amount: float, reason: str,
                                   significance: EventSignificance = EventSignificance.NORMAL):
        """Трекинг расходов валюты"""
        return await self.track_event(
            user_id=user_id,
            event_type=EventType.CURRENCY_SPENT,
            data={
                "currency_type": currency_type,
                "amount": amount,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            significance=significance
        )

    async def track_currency_earned(self, user_id: int, currency_type: str,
                                    amount: float, source: str):
        """Трекинг заработка валюты"""
        return await self.track_event(
            user_id=user_id,
            event_type=EventType.CURRENCY_EARNED,
            data={
                "currency_type": currency_type,
                "amount": amount,
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            significance=EventSignificance.NORMAL
        )

    async def track_specialist_hiring(self, user_id: int, specialist_type: str, cost: float):
        """Трекинг найма специалистов"""
        return await self.track_event(
            user_id=user_id,
            event_type=EventType.SPECIALIST_HIRED,
            data={
                "specialist_type": specialist_type,
                "cost": cost,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            significance=EventSignificance.NORMAL
        )

# Глобальный экземпляр
_event_tracker_instance: Optional[EventTracker] = None

async def get_event_tracker(client=None) -> EventTracker:
    """Получить глобальный экземпляр EventTracker"""
    global _event_tracker_instance

    if _event_tracker_instance is None:
        _event_tracker_instance = EventTracker(client=client)

    return _event_tracker_instance

logger.info("✅ Event Tracker module loaded")