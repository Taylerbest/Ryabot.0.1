# interfaces/telegram_bot/middlewares/user_activity_middleware.py
"""
Оптимизированный middleware с throttling
Обновляет last_active максимум раз в 2 минуты на пользователя
"""

import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from datetime import datetime

from adapters.database.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)


class UserActivityMiddleware(BaseMiddleware):
    """Отслеживает активность с throttling"""

    def __init__(self, throttle_seconds: int = 600):
        """
        Args:
            throttle_seconds: Минимальный интервал между обновлениями (10 минуты)
        """
        super().__init__()
        self.throttle_seconds = throttle_seconds
        self._last_updates: Dict[int, datetime] = {}

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        tg_user: User = data.get("event_from_user")
        if tg_user:
            try:
                # Обновляем только если прошло достаточно времени
                if self._should_update(tg_user.id):
                    await self._update_last_active(tg_user.id)
                    self._last_updates[tg_user.id] = datetime.now()

            except Exception as e:
                logger.error(f"Ошибка обновления активности {tg_user.id}: {e}")

        return await handler(event, data)

    def _should_update(self, user_id: int) -> bool:
        """Проверить нужно ли обновлять"""
        last_update = self._last_updates.get(user_id)

        if not last_update:
            return True  # Первое обновление

        elapsed = (datetime.now() - last_update).total_seconds()
        return elapsed >= self.throttle_seconds

    async def _update_last_active(self, user_id: int):
        """Обновить last_active в БД"""
        try:
            client = await get_supabase_client()
            await client.execute_query(
                table="users",
                operation="update",
                data={"last_active": datetime.now().isoformat()},
                filters={"user_id": user_id}
            )
            logger.debug(f"✅ Обновлена активность пользователя {user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка обновления {user_id}: {e}")
