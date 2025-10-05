# config/game_stats.py
"""
Сервис статистики бота для стартового экрана
"""

import logging
from datetime import datetime, timedelta
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
        """Получить количество онлайн пользователей (активны за последние 5 минут)"""
        try:
            await self._ensure_client()

            five_minutes_ago = (datetime.now() - timedelta(minutes=5)).isoformat()

            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"last_active__gte": five_minutes_ago}
            )

            return len(result) if result else 0

        except Exception as e:
            logger.error(f"Ошибка получения онлайн пользователей: {e}")
            return 0

    async def get_new_users_today(self) -> int:
        """Получить количество новых пользователей сегодня"""
        try:
            await self._ensure_client()

            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"created_at__gte": today}
            )

            return len(result) if result else 0

        except Exception as e:
            logger.error(f"Ошибка получения новых пользователей за день: {e}")
            return 0

    async def get_new_users_month(self) -> int:
        """Получить количество новых пользователей за месяц"""
        try:
            await self._ensure_client()

            month_ago = (datetime.now() - timedelta(days=30)).isoformat()

            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"created_at__gte": month_ago}
            )

            return len(result) if result else 0

        except Exception as e:
            logger.error(f"Ошибка получения новых пользователей за месяц: {e}")
            return 0

    async def get_quantum_pass_holders(self) -> int:
        """Получить количество обладателей Quantum Pass"""
        try:
            await self._ensure_client()

            now = datetime.now().isoformat()

            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"quantum_pass_until__gte": now}
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
            'new_users_today': await self.get_new_users_today(),
            'new_users_month': await self.get_new_users_month(),
            'quantum_pass_holders': await self.get_quantum_pass_holders()
        }


# Глобальный экземпляр
game_stats = GameStats()
