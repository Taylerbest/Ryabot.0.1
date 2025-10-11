# services/bank_service.py (ИСПРАВЛЕННАЯ ВЕРСИЯ ДЛЯ ВАШЕЙ СТРУКТУРЫ)
"""
Bank Service с правильной структурой пулов
"""

import logging
from decimal import Decimal
from typing import Tuple, Optional, Dict
from datetime import datetime, timezone

from adapters.database.supabase.client import get_supabase_client
from config.global_pools import (
    BANK_POOLS, calculate_current_rate, calculate_stars_to_ryabucks,
    calculate_buy_rbtc_cost, calculate_sell_rbtc_reward,
    TRANSACTION_LIMITS, RBTC_EQUIVALENT, STARS_PACKAGES
)

logger = logging.getLogger(__name__)

class BankService:
    def __init__(self):
        self.client = None

    async def _ensure_client(self):
        """Supabase клиент"""
        if not self.client:
            self.client = await get_supabase_client()

    async def get_bank_pools(self) -> Dict:
        """
        ИСПРАВЛЕНО: Работа с раздельными пулами game_bank_rbtc и game_bank_ryabucks
        """
        try:
            await self._ensure_client()

            # Получаем RBTC пул
            rbtc_pool_data = await self.client.execute_query(
                table="global_pools",
                operation="select",
                columns=["rbtc_amount"],
                filters={"pool_name": "game_bank_rbtc"},
                single=True
            )

            if rbtc_pool_data and rbtc_pool_data.get("rbtc_amount"):
                rbtc_pool = Decimal(str(rbtc_pool_data["rbtc_amount"]))
            else:
                rbtc_pool = BANK_POOLS["rbtc_pool"]
                logger.warning(f"RBTC пул не найден, используем дефолт: {rbtc_pool}")

            # Получаем рябаксов пул для обмена
            ryabucks_pool_data = await self.client.execute_query(
                table="global_pools",
                operation="select",
                columns=["ryabucks_amount"],
                filters={"pool_name": "game_bank_ryabucks"},
                single=True
            )

            if ryabucks_pool_data and ryabucks_pool_data.get("ryabucks_amount"):
                ryabucks_pool = Decimal(str(ryabucks_pool_data["ryabucks_amount"]))
            else:
                ryabucks_pool = BANK_POOLS["ryabucks_pool"]
                logger.warning(f"Рябаксов пул не найден, используем дефолт: {ryabucks_pool}")

            # Получаем ОБЩИЙ банк рябаксов (вся экономика)
            total_bank_data = await self.client.execute_query(
                table="global_pools",
                operation="select",
                columns=["ryabucks_amount"],
                filters={"pool_name": "total_bank_ryabucks"},
                single=True
            )

            if total_bank_data and total_bank_data.get("ryabucks_amount"):
                total_bank_ryabucks = Decimal(str(total_bank_data["ryabucks_amount"]))
            else:
                # Если нет записи - считаем сумму всех пулов КРОМЕ game_bank_ryabucks
                all_pools = await self.client.execute_query(
                    table="global_pools",
                    operation="select",
                    columns=["pool_name", "ryabucks_amount"]
                )

                total_bank_ryabucks = Decimal("0")
                if all_pools:
                    for pool in all_pools:
                        pool_name = pool.get("pool_name", "")
                        # Считаем все пулы КРОМЕ пула обмена
                        if pool_name != "game_bank_ryabucks":
                            amount = pool.get("ryabucks_amount", 0)
                            if amount:
                                total_bank_ryabucks += Decimal(str(amount))

                logger.info(f"total_bank_ryabucks рассчитан как сумма: {total_bank_ryabucks}")

            # Проверяем что пулы не нулевые
            if rbtc_pool <= 0:
                rbtc_pool = Decimal("1050000")
                logger.error("RBTC пул = 0! Используем дефолт")

            if ryabucks_pool <= 0:
                ryabucks_pool = Decimal("105000000")
                logger.error("Рябаксов пул = 0! Используем дефолт")

            # Рассчитываем курс по формуле x*y=k
            current_rate = calculate_current_rate(rbtc_pool, ryabucks_pool)

            logger.info(f"✅ Пулы: RBTC={rbtc_pool}, Обмен_рябаксы={ryabucks_pool}, Общий_банк={total_bank_ryabucks}, Курс={current_rate:.2f}")

            return {
                "rbtc_pool": rbtc_pool,
                "ryabucks_pool": ryabucks_pool,
                "current_rate": current_rate,
                "total_invested_golden_eggs": 0,
                "total_bank_ryabucks": total_bank_ryabucks
            }

        except Exception as e:
            logger.error(f"Ошибка получения пулов банка: {e}", exc_info=True)
            return {
                "rbtc_pool": BANK_POOLS["rbtc_pool"],
                "ryabucks_pool": BANK_POOLS["ryabucks_pool"],
                "current_rate": Decimal("100"),
                "total_invested_golden_eggs": 0,
                "total_bank_ryabucks": BANK_POOLS["ryabucks_pool"]
            }

    async def calculate_max_buyable_rbtc(self, user_ryabucks: int) -> Tuple[Decimal, int]:
        """Рассчитать максимум RBTC который можно купить"""
        pools = await self.get_bank_pools()
        rbtc_pool = pools["rbtc_pool"]
        ryabucks_pool = pools["ryabucks_pool"]
        current_rate = pools["current_rate"]

        if current_rate <= 0:
            current_rate = Decimal("100")

        max_by_money = Decimal(user_ryabucks) / current_rate
        max_by_pool = rbtc_pool * Decimal("0.99")
        max_buyable = min(max_by_money, max_by_pool)

        try:
            cost = calculate_buy_rbtc_cost(max_buyable, rbtc_pool, ryabucks_pool)
        except (ValueError, ZeroDivisionError) as e:
            logger.error(f"Ошибка расчета стоимости: {e}")
            cost = int(max_buyable * current_rate)

        return max_buyable, min(cost, user_ryabucks)

    async def buy_rbtc(self, user_id: int, amount: Decimal) -> Tuple[bool, str]:
        """Покупка RBTC за рябаксы"""
        try:
            await self._ensure_client()

            if amount <= TRANSACTION_LIMITS["min_rbtc_trade"]:
                return False, f"Минимум {TRANSACTION_LIMITS['min_rbtc_trade']} RBTC"

            user = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["ryabucks", "rbtc"],
                filters={"user_id": user_id},
                single=True
            )

            if not user:
                return False, "Пользователь не найден"

            user_ryabucks = user.get("ryabucks", 0)

            pools = await self.get_bank_pools()
            rbtc_pool = pools["rbtc_pool"]
            ryabucks_pool = pools["ryabucks_pool"]

            if rbtc_pool <= 0 or ryabucks_pool <= 0:
                return False, "Ошибка пулов банка. Обратитесь к администратору."

            if amount >= rbtc_pool:
                return False, f"В пуле недостаточно RBTC. Максимум: {float(rbtc_pool * Decimal('0.99')):.4f}"

            try:
                cost = calculate_buy_rbtc_cost(amount, rbtc_pool, ryabucks_pool)
            except (ValueError, ZeroDivisionError) as e:
                logger.error(f"Ошибка расчета стоимости покупки RBTC: {e}")
                return False, "Ошибка расчета стоимости."

            if user_ryabucks < cost:
                return False, f"Недостаточно рябаксов. Нужно: {cost:,}, есть: {user_ryabucks:,}"

            # Обновляем баланс пользователя
            new_user_ryabucks = user_ryabucks - cost
            new_user_rbtc = float(user.get("rbtc", 0)) + float(amount)

            await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "ryabucks": new_user_ryabucks,
                    "rbtc": new_user_rbtc
                },
                filters={"user_id": user_id}
            )

            # Обновляем RBTC пул
            new_rbtc_pool = rbtc_pool - amount
            await self.client.execute_query(
                table="global_pools",
                operation="update",
                data={
                    "rbtc_amount": float(new_rbtc_pool),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                filters={"pool_name": "game_bank_rbtc"}
            )

            # Обновляем рябаксов пул
            new_ryabucks_pool = ryabucks_pool + cost
            await self.client.execute_query(
                table="global_pools",
                operation="update",
                data={
                    "ryabucks_amount": int(new_ryabucks_pool),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                filters={"pool_name": "game_bank_ryabucks"}
            )

            # Логируем транзакцию
            new_rate = calculate_current_rate(new_rbtc_pool, new_ryabucks_pool)

            await self.client.execute_query(
                table="pool_transactions",
                operation="insert",
                data={
                    "pool_name": "game_bank_rbtc",
                    "transaction_type": "buy_rbtc",
                    "rbtc_amount": float(amount),
                    "ryabucks_amount": cost,
                    "user_id": user_id,
                    "description": f"Куплено {float(amount):.4f} RBTC по курсу {float(new_rate):.2f}"
                }
            )

            return True, f"✅ Куплено {float(amount):.4f} RBTC за {cost:,} рябаксов\n💱 Новый курс: 1 RBTC = {float(new_rate):.2f} рябаксов"

        except Exception as e:
            logger.error(f"Ошибка покупки RBTC для user {user_id}: {e}", exc_info=True)
            return False, f"Ошибка: {str(e)}"

    async def sell_rbtc(self, user_id: int, amount: Decimal) -> Tuple[bool, str]:
        """Продажа RBTC за рябаксы"""
        try:
            await self._ensure_client()

            if amount <= TRANSACTION_LIMITS["min_rbtc_trade"]:
                return False, f"Минимум {TRANSACTION_LIMITS['min_rbtc_trade']} RBTC"

            user = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["ryabucks", "rbtc"],
                filters={"user_id": user_id},
                single=True
            )

            if not user:
                return False, "Пользователь не найден"

            user_rbtc = Decimal(str(user.get("rbtc", 0)))

            if user_rbtc < amount:
                return False, f"Недостаточно RBTC. Нужно: {float(amount):.4f}, есть: {float(user_rbtc):.4f}"

            pools = await self.get_bank_pools()
            rbtc_pool = pools["rbtc_pool"]
            ryabucks_pool = pools["ryabucks_pool"]

            if rbtc_pool <= 0 or ryabucks_pool <= 0:
                return False, "Ошибка пулов банка"

            try:
                reward = calculate_sell_rbtc_reward(amount, rbtc_pool, ryabucks_pool)
            except (ValueError, ZeroDivisionError) as e:
                logger.error(f"Ошибка расчета продажи RBTC: {e}")
                return False, "Ошибка расчета"

            if reward > ryabucks_pool:
                return False, "В пуле недостаточно рябаксов"

            new_user_ryabucks = user.get("ryabucks", 0) + reward
            new_user_rbtc = float(user_rbtc - amount)

            await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "ryabucks": new_user_ryabucks,
                    "rbtc": new_user_rbtc
                },
                filters={"user_id": user_id}
            )

            # Обновляем RBTC пул
            new_rbtc_pool = rbtc_pool + amount
            await self.client.execute_query(
                table="global_pools",
                operation="update",
                data={
                    "rbtc_amount": float(new_rbtc_pool),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                filters={"pool_name": "game_bank_rbtc"}
            )

            # Обновляем рябаксов пул
            new_ryabucks_pool = ryabucks_pool - reward
            await self.client.execute_query(
                table="global_pools",
                operation="update",
                data={
                    "ryabucks_amount": int(new_ryabucks_pool),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                filters={"pool_name": "game_bank_ryabucks"}
            )

            new_rate = calculate_current_rate(new_rbtc_pool, new_ryabucks_pool)

            await self.client.execute_query(
                table="pool_transactions",
                operation="insert",
                data={
                    "pool_name": "game_bank_rbtc",
                    "transaction_type": "sell_rbtc",
                    "rbtc_amount": float(amount),
                    "ryabucks_amount": reward,
                    "user_id": user_id,
                    "description": f"Продано {float(amount):.4f} RBTC по курсу {float(new_rate):.2f}"
                }
            )

            return True, f"✅ Продано {float(amount):.4f} RBTC за {reward:,} рябаксов\n💱 Новый курс: 1 RBTC = {float(new_rate):.2f} рябаксов"

        except Exception as e:
            logger.error(f"Ошибка продажи RBTC для user {user_id}: {e}", exc_info=True)
            return False, f"Ошибка: {str(e)}"

    async def buy_ryabucks_with_stars(self, user_id: int, stars: int) -> Tuple[bool, str, int]:
        """Покупка рябаксов за Telegram Stars"""
        try:
            await self._ensure_client()

            pools = await self.get_bank_pools()
            current_rate = float(pools["current_rate"])

            if current_rate <= 0:
                current_rate = 100.0

            ryabucks_base = calculate_stars_to_ryabucks(stars, Decimal(current_rate))

            bonus_percent = 0
            for package in STARS_PACKAGES:
                if package["stars"] == stars:
                    bonus_percent = package["bonus"]
                    break

            bonus_amount = int(ryabucks_base * bonus_percent / 100.0)
            total_ryabucks = ryabucks_base + bonus_amount

            user = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["ryabucks"],
                filters={"user_id": user_id},
                single=True
            )

            if not user:
                return False, "Пользователь не найден", 0

            new_ryabucks = user.get("ryabucks", 0) + total_ryabucks

            await self.client.execute_query(
                table="users",
                operation="update",
                data={"ryabucks": new_ryabucks},
                filters={"user_id": user_id}
            )

            # Обновляем total_bank_ryabucks (добавляем новые рябаксы в экономику)
            total_bank_data = await self.client.execute_query(
                table="global_pools",
                operation="select",
                columns=["ryabucks_amount"],
                filters={"pool_name": "total_bank_ryabucks"},
                single=True
            )

            if total_bank_data:
                current_total = Decimal(str(total_bank_data.get("ryabucks_amount", 0)))
                new_total = current_total + total_ryabucks

                await self.client.execute_query(
                    table="global_pools",
                    operation="update",
                    data={
                        "ryabucks_amount": int(new_total),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    },
                    filters={"pool_name": "total_bank_ryabucks"}
                )

            await self.client.execute_query(
                table="pool_transactions",
                operation="insert",
                data={
                    "pool_name": "stars_purchase",
                    "transaction_type": "buy_ryabucks",
                    "rbtc_amount": 0,
                    "ryabucks_amount": total_ryabucks,
                    "user_id": user_id,
                    "description": f"Куплено {total_ryabucks:,} рябаксов за {stars} Stars"
                }
            )

            return True, f"Получено {total_ryabucks:,} рябаксов!", total_ryabucks

        except Exception as e:
            logger.error(f"Ошибка покупки за Stars для user {user_id}: {e}", exc_info=True)
            return False, f"Ошибка: {str(e)}", 0


bank_service = BankService()
logger.info("✅ BankService loaded (CORRECT STRUCTURE)")