# services/energy_service.py
"""
Energy Service - управление энергией игроков
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Конфигурация энергии
MAX_ENERGY = 100
ENERGY_REGEN_INTERVAL_MINUTES = 48  # Регенерация каждые 48 минут
ENERGY_PER_REGEN = 1  # +1 энергия за интервал
ENERGY_FROM_AD = 30  # +30 от просмотра рекламы

class EnergyService:
    """Сервис управления энергией"""

    def __init__(self, user_repository):
        self.user_repository = user_repository
        self.client = None
        logger.info("EnergyService инициализирован")

    async def _ensure_client(self):
        """Подключаем клиент БД если нужен"""
        if not self.client:
            from adapters.database.supabase.client import get_supabase_client
            self.client = await get_supabase_client()

    async def get_energy_info(self, user_id: int) -> Dict[str, Any]:
        """
        Получить информацию об энергии пользователя

        Returns:
            {
                "current": 45,
                "max": 100,
                "regen_in_minutes": 15,
                "regen_rate": "1 энергия / 48 минут"
            }
        """
        try:
            await self._ensure_client()

            # Получаем пользователя
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return {
                    "current": 0,
                    "max": MAX_ENERGY,
                    "regen_in_minutes": 0,
                    "regen_rate": f"{ENERGY_PER_REGEN} / {ENERGY_REGEN_INTERVAL_MINUTES} мин"
                }

            # Регенерируем энергию если прошло время
            current_energy = await self._regenerate_energy(user_id, user.energy.current)

            # Вычисляем время до следующей регенерации
            last_update = user.energy.last_update if hasattr(user.energy, 'last_update') else datetime.now(timezone.utc)
            time_since_update = (datetime.now(timezone.utc) - last_update).total_seconds() / 60
            regen_in_minutes = max(0, ENERGY_REGEN_INTERVAL_MINUTES - int(time_since_update % ENERGY_REGEN_INTERVAL_MINUTES))

            return {
                "current": current_energy,
                "max": MAX_ENERGY,
                "regen_in_minutes": regen_in_minutes,
                "regen_rate": f"{ENERGY_PER_REGEN} / {ENERGY_REGEN_INTERVAL_MINUTES} мин"
            }

        except Exception as e:
            logger.error(f"Ошибка получения информации об энергии для {user_id}: {e}")
            return {
                "current": 0,
                "max": MAX_ENERGY,
                "regen_in_minutes": 0,
                "regen_rate": f"{ENERGY_PER_REGEN} / {ENERGY_REGEN_INTERVAL_MINUTES} мин"
            }

    async def _regenerate_energy(self, user_id: int, current_energy: int) -> int:
        """
        Регенерация энергии на основе прошедшего времени

        Returns:
            Новое значение энергии
        """
        try:
            await self._ensure_client()

            # Получаем время последнего обновления
            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["energy", "energy_last_update"],
                filters={"user_id": user_id},
                single=True
            )

            if not result:
                return current_energy

            energy = result.get("energy", current_energy)
            last_update_str = result.get("energy_last_update")

            # Если уже максимум - ничего не делаем
            if energy >= MAX_ENERGY:
                return MAX_ENERGY

            # Парсим время последнего обновления
            if last_update_str:
                last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
            else:
                last_update = datetime.now(timezone.utc)

            # Вычисляем сколько времени прошло
            time_passed = datetime.now(timezone.utc) - last_update
            minutes_passed = time_passed.total_seconds() / 60

            # Вычисляем сколько энергии регенерировалось
            energy_regenerated = int(minutes_passed / ENERGY_REGEN_INTERVAL_MINUTES) * ENERGY_PER_REGEN

            if energy_regenerated > 0:
                new_energy = min(energy + energy_regenerated, MAX_ENERGY)

                # Обновляем в БД
                await self.client.execute_query(
                    table="users",
                    operation="update",
                    data={
                        "energy": new_energy,
                        "energy_last_update": datetime.now(timezone.utc).isoformat()
                    },
                    filters={"user_id": user_id}
                )

                logger.info(f"⚡ Энергия регенерирована для {user_id}: {energy} -> {new_energy}")
                return new_energy

            return energy

        except Exception as e:
            logger.error(f"Ошибка регенерации энергии для {user_id}: {e}")
            return current_energy

    async def can_perform_action(self, user_id: int, energy_cost: int) -> Tuple[bool, str]:
        """
        Проверить достаточно ли энергии для действия

        Returns:
            (можно_выполнить, сообщение)
        """
        try:
            energy_info = await self.get_energy_info(user_id)
            current_energy = energy_info["current"]

            if current_energy >= energy_cost:
                return True, f"Достаточно энергии: {current_energy}/{energy_cost}"
            else:
                regen_time = energy_info["regen_in_minutes"]
                return False, f"Недостаточно энергии! Есть: {current_energy}, нужно: {energy_cost}. Следующая регенерация через {regen_time} мин"

        except Exception as e:
            logger.error(f"Ошибка проверки энергии для {user_id}: {e}")
            return False, "Ошибка проверки энергии"

    async def consume_energy(self, user_id: int, energy_cost: int) -> bool:
        """
        Списать энергию за действие

        Returns:
            True если успешно списано
        """
        try:
            await self._ensure_client()

            # Проверяем возможность
            can_perform, message = await self.can_perform_action(user_id, energy_cost)

            if not can_perform:
                logger.warning(f"Недостаточно энергии для {user_id}: {message}")
                return False

            # Получаем текущую энергию
            user = await self.user_repository.get_by_id(user_id)
            current_energy = user.energy.current

            # Списываем
            new_energy = max(0, current_energy - energy_cost)

            await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "energy": new_energy,
                    "energy_last_update": datetime.now(timezone.utc).isoformat()
                },
                filters={"user_id": user_id}
            )

            logger.info(f"⚡ Энергия списана для {user_id}: -{energy_cost} ({current_energy} -> {new_energy})")
            return True

        except Exception as e:
            logger.error(f"Ошибка списания энергии для {user_id}: {e}")
            return False

    async def restore_energy(self, user_id: int, amount: int, reason: str = "restore") -> bool:
        """
        Восстановить энергию (от рекламы, покупки и т.д.)

        Returns:
            True если успешно восстановлено
        """
        try:
            await self._ensure_client()

            # Получаем текущую энергию
            user = await self.user_repository.get_by_id(user_id)
            current_energy = user.energy.current

            # Восстанавливаем
            new_energy = min(current_energy + amount, MAX_ENERGY)

            await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "energy": new_energy,
                    "energy_last_update": datetime.now(timezone.utc).isoformat()
                },
                filters={"user_id": user_id}
            )

            logger.info(f"⚡ Энергия восстановлена для {user_id}: +{amount} ({current_energy} -> {new_energy}) | {reason}")
            return True

        except Exception as e:
            logger.error(f"Ошибка восстановления энергии для {user_id}: {e}")
            return False

    async def watch_ad_for_energy(self, user_id: int) -> Tuple[bool, str]:
        """
        Получить энергию за просмотр рекламы

        Returns:
            (успех, сообщение)
        """
        try:
            # TODO: Добавить проверку времени последнего просмотра (cooldown)
            # TODO: Интегрировать с Ad Network

            success = await self.restore_energy(user_id, ENERGY_FROM_AD, "ad_watched")

            if success:
                return True, f"+{ENERGY_FROM_AD} энергии за просмотр рекламы!"
            else:
                return False, "Не удалось начислить энергию"

        except Exception as e:
            logger.error(f"Ошибка начисления энергии за рекламу для {user_id}: {e}")
            return False, "Техническая ошибка"

logger.info("EnergyService module loaded")