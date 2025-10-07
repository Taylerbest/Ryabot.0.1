# config/game_stats.py
"""
Сервис статистики бота для стартового экрана
"""

import logging
from datetime import datetime, timedelta, timezone  # ✅ Добавили timezone
from adapters.database.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)


class GameStats:
    """Класс для получения статистики игры"""

    def __init__(self):
        self.bot_start_time = datetime.now()
        self.client = None

    async def _ensure_client(self):
        """Обеспечиваем подключение к БД"""
        if not self.client:
            self.client = await get_supabase_client()

    def get_uptime(self) -> dict:
        """Получить время работы бота"""
        now = datetime.now()
        uptime_delta = now - self.bot_start_time

        days = uptime_delta.days
        hours = uptime_delta.seconds // 3600
        minutes = (uptime_delta.seconds % 3600) // 60

        return {
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'total_seconds': int(uptime_delta.total_seconds())
        }

    async def get_total_users(self) -> int:
        """Получить общее количество пользователей"""
        try:
            await self._ensure_client()

            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
            )

            return len(result) if result else 0

        except Exception as e:
            logger.error(f"Ошибка получения общего количества пользователей: {e}")
            return 0

    async def get_online_users(self) -> int:
        """Получить количество онлайн пользователей (активны за последний час)"""
        try:
            await self._ensure_client()

            # ✅ ИСПОЛЬЗУЕМ UTC timezone
            cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"last_active": {"gte": cutoff.isoformat()}}
            )

            count = len(result) if result else 0
            logger.info(f"🔍 get_online_users: cutoff={cutoff.isoformat()}, count={count}")

            return count

        except Exception as e:
            logger.error(f"Ошибка получения онлайн пользователей: {e}")
            return 0

    async def get_new_users_today(self) -> int:
        """Получить количество новых пользователей сегодня"""
        try:
            await self._ensure_client()

            # ✅ ИСПОЛЬЗУЕМ UTC timezone
            today = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"created_at": {"gte": today.isoformat()}}
            )

            count = len(result) if result else 0
            logger.info(f"🔍 get_new_users_today: today={today.isoformat()}, count={count}")

            return count

        except Exception as e:
            logger.error(f"Ошибка получения новых пользователей за день: {e}")
            return 0

    async def get_new_users_week(self) -> int:
        """Получить количество новых пользователей за неделю"""
        try:
            await self._ensure_client()

            # ✅ ИСПОЛЬЗУЕМ UTC timezone
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)

            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"created_at": {"gte": week_ago.isoformat()}}
            )

            return len(result) if result else 0

        except Exception as e:
            logger.error(f"Ошибка получения новых пользователей за неделю: {e}")
            return 0

    async def get_new_users_month(self) -> int:
        """Получить количество новых пользователей за месяц"""
        try:
            await self._ensure_client()

            # ✅ ИСПОЛЬЗУЕМ UTC timezone
            month_start = datetime.now(timezone.utc).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"created_at": {"gte": month_start.isoformat()}}
            )

            return len(result) if result else 0

        except Exception as e:
            logger.error(f"Ошибка получения новых пользователей за месяц: {e}")
            return 0

    async def get_quantum_pass_holders(self) -> int:
        """Получить количество обладателей Quantum Pass"""
        try:
            await self._ensure_client()

            # ✅ ИСПОЛЬЗУЕМ UTC timezone
            now = datetime.now(timezone.utc)

            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"quantum_pass_until": {"gte": now.isoformat()}}
            )

            return len(result) if result else 0

        except Exception as e:
            logger.error(f"Ошибка получения держателей Quantum Pass: {e}")
            return 0

    async def get_all_stats(self) -> dict:
        """Получить все статистики разом"""
        return {
            'uptime': self.get_uptime(),
            'total_users': await self.get_total_users(),
            'online_users': await self.get_online_users(),
            'new_users_today': await self.get_new_users_today(),  # ✅ Исправлено
            'new_users_week': await self.get_new_users_week(),  # ✅ Исправлено
            'new_users_month': await self.get_new_users_month(),  # ✅ Исправлено
            'quantum_pass_holders': await self.get_quantum_pass_holders()
        }


# Глобальный экземпляр
game_stats = GameStats()
