# middlewares/energy_middleware.py
"""
Middleware для системы энергии из GDD
"""

import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from datetime import datetime, timedelta

from adapters.database.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)


class EnergyMiddleware(BaseMiddleware):
    """
    Middleware для автоматического восстановления энергии
    Согласно GDD: энергия восстанавливается каждые 15 минут на 1 единицу
    """

    def __init__(self):
        super().__init__()
        self.energy_regen_minutes = 15  # Каждые 15 минут +1 энергия (48 минут на полную)
        self.max_energy = 30  # Максимум 30 энергии
        self.ad_energy_bonus = 30  # +30 энергии за рекламу
        self.daily_ad_limit = 3  # Максимум 3 рекламы в день

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        """Обработка события с регенерацией энергии"""

        # Получаем пользователя
        user: User = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        try:
            # Обновляем энергию пользователя
            await self._regenerate_user_energy(user.id)

        except Exception as e:
            logger.error(f"Ошибка в energy middleware для {user.id}: {e}")

        return await handler(event, data)

    async def _regenerate_user_energy(self, user_id: int):
        """Регенерация энергии пользователя"""
        try:
            client = await get_supabase_client()

            # Получаем текущие данные пользователя
            user_data = await client.execute_query(
                table="users",
                operation="select",
                columns=["energy", "energy_max", "last_active"],
                filters={"user_id": user_id},
                single=True
            )

            if not user_data:
                return

            current_energy = user_data.get('energy', self.max_energy)
            max_energy = user_data.get('energy_max', self.max_energy)
            last_active_str = user_data.get('last_active')

            # Если энергия уже максимальная, ничего не делаем
            if current_energy >= max_energy:
                await self._update_last_active(client, user_id)
                return

            # Парсим последнюю активность
            if not last_active_str:
                await self._update_last_active(client, user_id)
                return

            try:
                if isinstance(last_active_str, str):
                    if '.' in last_active_str:
                        last_active = datetime.fromisoformat(last_active_str.split('.')[0])
                    else:
                        last_active = datetime.fromisoformat(last_active_str)
                else:
                    last_active = last_active_str

                # Убираем timezone info если есть
                if hasattr(last_active, 'tzinfo') and last_active.tzinfo is not None:
                    last_active = last_active.replace(tzinfo=None)

            except (ValueError, AttributeError) as e:
                logger.warning(f"Ошибка парсинга времени для {user_id}: {e}")
                await self._update_last_active(client, user_id)
                return

            # Вычисляем прошедшее время
            now = datetime.now()
            time_diff = now - last_active
            minutes_passed = time_diff.total_seconds() / 60

            # Вычисляем сколько энергии должно восстановиться
            energy_regen_cycles = int(minutes_passed // self.energy_regen_minutes)

            if energy_regen_cycles > 0:
                # Рассчитываем новое количество энергии
                new_energy = min(current_energy + energy_regen_cycles, max_energy)

                if new_energy != current_energy:
                    # Обновляем энергию и время
                    await client.execute_query(
                        table="users",
                        operation="update",
                        data={
                            "energy": new_energy,
                            "last_active": now.isoformat()
                        },
                        filters={"user_id": user_id}
                    )

                    logger.debug(f"Энергия пользователя {user_id}: {current_energy} → {new_energy}")
                else:
                    # Обновляем только время активности
                    await self._update_last_active(client, user_id)
            else:
                # Обновляем время активности
                await self._update_last_active(client, user_id)

        except Exception as e:
            logger.error(f"Ошибка регенерации энергии для {user_id}: {e}")

    async def _update_last_active(self, client, user_id: int):
        """Обновить время последней активности"""
        try:
            await client.execute_query(
                table="users",
                operation="update",
                data={"last_active": datetime.now().isoformat()},
                filters={"user_id": user_id}
            )
        except Exception as e:
            logger.error(f"Ошибка обновления last_active для {user_id}: {e}")


# === ФУНКЦИИ ДЛЯ РАБОТЫ С ЭНЕРГИЕЙ ===

async def get_user_energy_info(user_id: int) -> dict:
    """Получить информацию об энергии пользователя"""
    try:
        client = await get_supabase_client()

        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["energy", "energy_max", "last_active"],
            filters={"user_id": user_id},
            single=True
        )

        if not user_data:
            return {
                "current": 30,
                "maximum": 30,
                "minutes_to_next": 0,
                "minutes_to_full": 0
            }

        current = user_data.get('energy', 30)
        maximum = user_data.get('energy_max', 30)

        # Время до следующей регенерации
        last_active_str = user_data.get('last_active')
        minutes_to_next = 0
        minutes_to_full = 0

        if last_active_str and current < maximum:
            try:
                if isinstance(last_active_str, str):
                    if '.' in last_active_str:
                        last_active = datetime.fromisoformat(last_active_str.split('.')[0])
                    else:
                        last_active = datetime.fromisoformat(last_active_str)
                else:
                    last_active = last_active_str

                if hasattr(last_active, 'tzinfo') and last_active.tzinfo is not None:
                    last_active = last_active.replace(tzinfo=None)

                now = datetime.now()
                time_diff = now - last_active
                minutes_passed = time_diff.total_seconds() / 60

                # Время до следующей регенерации
                minutes_to_next = max(0, 15 - (minutes_passed % 15))

                # Время до полного восстановления
                energy_needed = maximum - current
                if energy_needed > 0:
                    minutes_to_full = (energy_needed * 15) - (minutes_passed % 15)
                    minutes_to_full = max(0, minutes_to_full)

            except Exception:
                minutes_to_next = 15
                minutes_to_full = (maximum - current) * 15

        return {
            "current": current,
            "maximum": maximum,
            "minutes_to_next": int(minutes_to_next),
            "minutes_to_full": int(minutes_to_full)
        }

    except Exception as e:
        logger.error(f"Ошибка получения энергии для {user_id}: {e}")
        return {
            "current": 30,
            "maximum": 30,
            "minutes_to_next": 0,
            "minutes_to_full": 0
        }


async def spend_energy(user_id: int, amount: int) -> tuple[bool, str]:
    """
    Потратить энергию
    Возвращает (success, message)
    """
    try:
        client = await get_supabase_client()

        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["energy"],
            filters={"user_id": user_id},
            single=True
        )

        if not user_data:
            return False, "Пользователь не найден"

        current_energy = user_data.get('energy', 0)

        if current_energy < amount:
            return False, f"Недостаточно энергии! Нужно {amount}, у вас {current_energy}"

        # Списываем энергию
        new_energy = current_energy - amount
        await client.execute_query(
            table="users",
            operation="update",
            data={"energy": new_energy},
            filters={"user_id": user_id}
        )

        return True, f"Потрачено {amount} энергии"

    except Exception as e:
        logger.error(f"Ошибка трат энергии для {user_id}: {e}")
        return False, "Ошибка системы энергии"


async def restore_energy_from_ad(user_id: int) -> tuple[bool, str]:
    """
    Восстановить энергию за просмотр рекламы (заглушка для MVP)
    """
    try:
        client = await get_supabase_client()

        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["energy", "energy_max"],
            filters={"user_id": user_id},
            single=True
        )

        if not user_data:
            return False, "Пользователь не найден"

        current_energy = user_data.get('energy', 30)
        max_energy = user_data.get('energy_max', 30)

        if current_energy >= max_energy:
            return False, "Энергия уже максимальная"

        # Добавляем энергию за "рекламу"
        new_energy = min(current_energy + 30, max_energy)

        await client.execute_query(
            table="users",
            operation="update",
            data={"energy": new_energy},
            filters={"user_id": user_id}
        )

        energy_gained = new_energy - current_energy

        return True, f"Получено {energy_gained} энергии за просмотр рекламы!"

    except Exception as e:
        logger.error(f"Ошибка восстановления энергии для {user_id}: {e}")
        return False, "Ошибка системы энергии"


def format_energy_time(minutes: int) -> str:
    """Форматирование времени для энергии"""
    if minutes <= 0:
        return "сейчас"

    hours = minutes // 60
    mins = minutes % 60

    if hours > 0:
        return f"{hours}ч {mins}м"
    else:
        return f"{mins}м"