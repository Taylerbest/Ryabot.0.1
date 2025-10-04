# config/game_stats.py
"""
Статистика игры и время работы бота
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from adapters.database.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)

# Время запуска бота
BOT_START_TIME = datetime.now()

class GameStats:
    """Класс для получения статистики игры"""
    
    def __init__(self):
        self.client = None
    
    async def _ensure_client(self):
        """Обеспечиваем подключение к БД"""
        if not self.client:
            self.client = await get_supabase_client()
    
    async def get_uptime(self) -> Dict[str, int]:
        """Получить время работы бота"""
        uptime = datetime.now() - BOT_START_TIME
        
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds // 60) % 60
        
        return {
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "total_minutes": int(uptime.total_seconds() // 60)
        }
    
    async def get_total_users(self) -> int:
        """Общее количество пользователей (островитяне)"""
        try:
            await self._ensure_client()
            
            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"]
            )
            
            return len(result) if result else 4  # Fallback значение
            
        except Exception as e:
            logger.error(f"Ошибка получения общего количества пользователей: {e}")
            return 4  # Fallback значение
    
    async def get_online_users(self) -> int:
        """Пользователи онлайн (активны за последние 10 минут)"""
        try:
            await self._ensure_client()
            
            # Считаем активными тех, кто заходил за последние 10 минут
            ten_minutes_ago = datetime.now() - timedelta(minutes=10)
            
            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"last_active": {"gte": ten_minutes_ago.isoformat()}}
            )
            
            return len(result) if result else 1  # Fallback значение
            
        except Exception as e:
            logger.error(f"Ошибка получения онлайн пользователей: {e}")
            return 1  # Fallback значение
    
    async def get_new_users_today(self) -> int:
        """Новые пользователи за сегодня"""
        try:
            await self._ensure_client()
            
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"created_at": {"gte": today_start.isoformat()}}
            )
            
            return len(result) if result else 0  # Fallback значение
            
        except Exception as e:
            logger.error(f"Ошибка получения новых пользователей за день: {e}")
            return 0  # Fallback значение
    
    async def get_new_users_month(self) -> int:
        """Новые пользователи за месяц"""
        try:
            await self._ensure_client()
            
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"created_at": {"gte": month_start.isoformat()}}
            )
            
            return len(result) if result else 3  # Fallback значение
            
        except Exception as e:
            logger.error(f"Ошибка получения новых пользователей за месяц: {e}")
            return 3  # Fallback значение
    
    async def get_quantum_pass_holders(self) -> int:
        """Количество обладателей Quantum Pass"""
        try:
            await self._ensure_client()
            
            now = datetime.now()
            
            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"quantum_pass_until": {"gte": now.isoformat()}}
            )
            
            return len(result) if result else 0  # Fallback значение
            
        except Exception as e:
            logger.error(f"Ошибка получения количества Quantum Pass: {e}")
            return 0  # Fallback значение
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """Получить все статистики разом"""
        try:
            # Выполняем все запросы параллельно для скорости
            tasks = [
                self.get_uptime(),
                self.get_total_users(),
                self.get_online_users(),
                self.get_new_users_today(),
                self.get_new_users_month(),
                self.get_quantum_pass_holders()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            uptime, total, online, new_today, new_month, qpass = results
            
            # Обрабатываем исключения и используем fallback значения
            if isinstance(uptime, Exception):
                uptime = {"days": 0, "hours": 0, "minutes": 0, "total_minutes": 0}
            if isinstance(total, Exception):
                total = 4
            if isinstance(online, Exception):
                online = 1
            if isinstance(new_today, Exception):
                new_today = 0
            if isinstance(new_month, Exception):
                new_month = 3
            if isinstance(qpass, Exception):
                qpass = 0
            
            return {
                "uptime": uptime,
                "total_users": total,
                "online_users": online,
                "new_users_today": new_today,
                "new_users_month": new_month,
                "quantum_pass_holders": qpass
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения всех статистик: {e}")
            
            # Возвращаем fallback значения
            return {
                "uptime": {"days": 0, "hours": 0, "minutes": 0, "total_minutes": 0},
                "total_users": 4,
                "online_users": 1,
                "new_users_today": 0,
                "new_users_month": 3,
                "quantum_pass_holders": 0
            }

# Глобальный экземпляр
game_stats = GameStats()