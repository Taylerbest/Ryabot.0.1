"""
Сервис банка (Рябанк) для управления обменом RBTC ↔ Рябаксы
с механикой DEX (динамический курс)
"""
import logging
from decimal import Decimal
from typing import Tuple, Optional, Dict
from datetime import datetime

from adapters.database.supabase.client import get_supabase_client
from config.global_pools import (
    BANK_POOLS,
    calculate_current_rate,
    calculate_stars_to_ryabucks,
    calculate_buy_rbtc_cost,
    calculate_sell_rbtc_reward,
    TRANSACTION_LIMITS,
    RBTC_EQUIVALENT,
    STARS_PACKAGES
)

logger = logging.getLogger(__name__)


class BankService:
    """Сервис для операций с игровым банком"""

    def __init__(self):
        self.client = None

    async def _ensure_client(self):
        """Инициализация клиента Supabase"""
        if not self.client:
            self.client = await get_supabase_client()

    async def get_bank_pools(self) -> Dict:
        """
        Получить текущее состояние банковских пулов

        Returns:
            Dict с rbtc_pool, ryabucks_pool, current_rate, total_invested_golden_eggs
        """
        try:
            await self._ensure_client()

            # Получить пулы банка из БД
            pools = await self.client.execute_query(
                table="global_pools",
                operation="select",
                filters={"pool_type": "bank"}
            )

            rbtc_pool = Decimal('0')
            ryabucks_pool = Decimal('0')

            for pool in pools:
                if pool['pool_name'] == 'game_bank_rbtc':
                    rbtc_pool = Decimal(str(pool['rbtc_amount']))
                elif pool['pool_name'] == 'game_bank_ryabucks':
                    ryabucks_pool = Decimal(str(pool['ryabucks_amount']))

            # Статистика
            stats = await self.client.execute_query(
                table="pool_statistics",
                operation="select",
                single=True
            )

            total_invested = stats.get('total_golden_eggs_invested', 0) if stats else 0

            # Рассчитать текущий курс
            current_rate = calculate_current_rate(rbtc_pool, ryabucks_pool)

            return {
                'rbtc_pool': rbtc_pool,
                'ryabucks_pool': ryabucks_pool,
                'current_rate': current_rate,
                'total_invested_golden_eggs': total_invested
            }

        except Exception as e:
            logger.error(f"Ошибка получения пулов банка: {e}")
            # Fallback на начальные значения
            return {
                'rbtc_pool': BANK_POOLS['rbtc_pool'],
                'ryabucks_pool': BANK_POOLS['ryabucks_pool'],
                'current_rate': Decimal('100'),
                'total_invested_golden_eggs': 0
            }

    async def calculate_max_buyable_rbtc(self, user_ryabucks: int) -> Tuple[Decimal, int]:
        """
        Рассчитать максимальное количество RBTC для покупки

        Args:
            user_ryabucks: Рябаксы пользователя

        Returns:
            (max_rbtc, cost_ryabucks)
        """
        pools = await self.get_bank_pools()
        rbtc_pool = pools['rbtc_pool']
        ryabucks_pool = pools['ryabucks_pool']

        # Максимум по деньгам (простое деление по текущему курсу)
        current_rate = pools['current_rate']
        max_by_money = Decimal(user_ryabucks) / current_rate

        # Максимум по пулу (можно купить почти весь пул, оставляя минимум)
        max_by_pool = rbtc_pool * Decimal('0.99')  # максимум 99% пула

        max_buyable = min(max_by_money, max_by_pool)

        # Рассчитать реальную стоимость по AMM
        try:
            cost = calculate_buy_rbtc_cost(max_buyable, rbtc_pool, ryabucks_pool)
        except ValueError:
            cost = int(max_buyable * current_rate)

        return max_buyable, min(cost, user_ryabucks)

    async def buy_rbtc(self, user_id: int, amount: Decimal) -> Tuple[bool, str]:
        """
        Купить RBTC за рябаксы с динамическим курсом (AMM)

        Args:
            user_id: ID пользователя
            amount: Количество RBTC для покупки

        Returns:
            (success, message)
        """
        try:
            await self._ensure_client()

            # Проверка лимитов
            if amount < TRANSACTION_LIMITS['min_rbtc_trade']:
                return False, f"Минимальная сумма: {TRANSACTION_LIMITS['min_rbtc_trade']} RBTC"

            if amount > TRANSACTION_LIMITS['max_rbtc_trade']:
                return False, f"Максимальная сумма: {TRANSACTION_LIMITS['max_rbtc_trade']} RBTC"

            # Получить пулы
            pools = await self.get_bank_pools()
            rbtc_pool = pools['rbtc_pool']
            ryabucks_pool = pools['ryabucks_pool']

            # Проверка достаточности в пуле
            if amount >= rbtc_pool:
                return False, f"В банке недостаточно RBTC. Доступно: {rbtc_pool:.4f}"

            # Рассчитать стоимость по AMM
            cost = calculate_buy_rbtc_cost(amount, rbtc_pool, ryabucks_pool)

            # Получить баланс пользователя
            user = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["ryabucks", "rbtc"],
                filters={"user_id": user_id},
                single=True
            )

            if not user:
                return False, "Пользователь не найден"

            user_ryabucks = user.get('ryabucks', 0)
            if user_ryabucks < cost:
                return False, f"Недостаточно рябаксов. Нужно: {cost:,}, есть: {user_ryabucks:,}"

            # Обновить пулы банка
            new_rbtc_pool = rbtc_pool - amount
            new_ryabucks_pool = ryabucks_pool + cost

            await self.client.execute_query(
                table="global_pools",
                operation="update",
                data={"rbtc_amount": float(new_rbtc_pool)},
                filters={"pool_name": "game_bank_rbtc"}
            )

            await self.client.execute_query(
                table="global_pools",
                operation="update",
                data={"ryabucks_amount": int(new_ryabucks_pool)},
                filters={"pool_name": "game_bank_ryabucks"}
            )

            # Обновить баланс пользователя
            new_user_ryabucks = user_ryabucks - cost
            new_user_rbtc = float(user.get('rbtc', 0)) + float(amount)

            await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "ryabucks": new_user_ryabucks,
                    "rbtc": new_user_rbtc
                },
                filters={"user_id": user_id}
            )

            # Записать транзакцию
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
                    "description": f"Покупка {amount:.4f} RBTC по курсу {new_rate:.2f}"
                }
            )

            return True, f"✅ Куплено {amount:.4f} 💠 RBTC за {cost:,} 💵\n\nНовый курс: 1 💠 = {new_rate:.2f} 💵"

        except Exception as e:
            logger.error(f"Ошибка покупки RBTC для user {user_id}: {e}")
            return False, f"Произошла ошибка: {str(e)}"

    async def sell_rbtc(self, user_id: int, amount: Decimal) -> Tuple[bool, str]:
        """
        Продать RBTC за рябаксы с динамическим курсом (AMM)

        Args:
            user_id: ID пользователя
            amount: Количество RBTC для продажи

        Returns:
            (success, message)
        """
        try:
            await self._ensure_client()

            # Проверка лимитов
            if amount < TRANSACTION_LIMITS['min_rbtc_trade']:
                return False, f"Минимальная сумма: {TRANSACTION_LIMITS['min_rbtc_trade']} RBTC"

            # Получить пулы
            pools = await self.get_bank_pools()
            rbtc_pool = pools['rbtc_pool']
            ryabucks_pool = pools['ryabucks_pool']

            # Рассчитать награду по AMM
            reward = calculate_sell_rbtc_reward(amount, rbtc_pool, ryabucks_pool)

            # Проверка достаточности рябаксов в пуле
            if reward > ryabucks_pool:
                return False, f"В банке недостаточно рябаксов. Доступно: {int(ryabucks_pool):,}"

            # Получить баланс пользователя
            user = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["ryabucks", "rbtc"],
                filters={"user_id": user_id},
                single=True
            )

            if not user:
                return False, "Пользователь не найден"

            user_rbtc = Decimal(str(user.get('rbtc', 0)))
            if user_rbtc < amount:
                return False, f"Недостаточно RBTC. Нужно: {amount:.4f}, есть: {user_rbtc:.4f}"

            # Обновить пулы банка
            new_rbtc_pool = rbtc_pool + amount
            new_ryabucks_pool = ryabucks_pool - reward

            await self.client.execute_query(
                table="global_pools",
                operation="update",
                data={"rbtc_amount": float(new_rbtc_pool)},
                filters={"pool_name": "game_bank_rbtc"}
            )

            await self.client.execute_query(
                table="global_pools",
                operation="update",
                data={"ryabucks_amount": int(new_ryabucks_pool)},
                filters={"pool_name": "game_bank_ryabucks"}
            )

            # Обновить баланс пользователя
            new_user_ryabucks = user.get('ryabucks', 0) + reward
            new_user_rbtc = float(user_rbtc) - float(amount)

            await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "ryabucks": new_user_ryabucks,
                    "rbtc": new_user_rbtc
                },
                filters={"user_id": user_id}
            )

            # Записать транзакцию
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
                    "description": f"Продажа {amount:.4f} RBTC по курсу {new_rate:.2f}"
                }
            )

            return True, f"✅ Продано {amount:.4f} 💠 RBTC за {reward:,} 💵\n\nНовый курс: 1 💠 = {new_rate:.2f} 💵"

        except Exception as e:
            logger.error(f"Ошибка продажи RBTC для user {user_id}: {e}")
            return False, f"Произошла ошибка: {str(e)}"

    async def buy_ryabucks_with_stars(
            self,
            user_id: int,
            stars: int
    ) -> Tuple[bool, str, int]:
        """
        Купить рябаксы за Telegram Stars по текущему курсу

        Args:
            user_id: ID пользователя
            stars: Количество Stars

        Returns:
            (success, message, ryabucks_amount)
        """
        try:
            await self._ensure_client()

            # Проверка лимитов
            if stars < TRANSACTION_LIMITS['min_stars_purchase']:
                return False, f"Минимум {TRANSACTION_LIMITS['min_stars_purchase']} ⭐", 0

            if stars > TRANSACTION_LIMITS['max_stars_purchase']:
                return False, f"Максимум {TRANSACTION_LIMITS['max_stars_purchase']} ⭐", 0

            # Получить текущий курс
            pools = await self.get_bank_pools()
            current_rate = pools['current_rate']

            # Рассчитать сколько рябаксов по формуле
            ryabucks_base = calculate_stars_to_ryabucks(stars, current_rate)

            # Применить бонус если есть
            bonus_percent = 0
            for package in STARS_PACKAGES:
                if stars >= package['stars']:
                    bonus_percent = package['bonus']

            bonus_amount = int(ryabucks_base * bonus_percent / 100)
            total_ryabucks = ryabucks_base + bonus_amount

            # Обновить баланс пользователя
            user = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["ryabucks"],
                filters={"user_id": user_id},
                single=True
            )

            if not user:
                return False, "Пользователь не найден", 0

            new_ryabucks = user.get('ryabucks', 0) + total_ryabucks

            await self.client.execute_query(
                table="users",
                operation="update",
                data={"ryabucks": new_ryabucks},
                filters={"user_id": user_id}
            )

            # Записать транзакцию
            await self.client.execute_query(
                table="pool_transactions",
                operation="insert",
                data={
                    "pool_name": "game_bank_ryabucks",
                    "transaction_type": "buy_ryabucks_stars",
                    "rbtc_amount": 0,
                    "ryabucks_amount": total_ryabucks,
                    "user_id": user_id,
                    "description": f"Покупка за {stars} ⭐ (эквивалент {RBTC_EQUIVALENT * stars / 100:.2f} RBTC по курсу {current_rate:.2f})"
                }
            )

            bonus_text = f"\n🎁 Бонус +{bonus_percent}%: {bonus_amount:,} 💵" if bonus_amount > 0 else ""

            return True, f"✅ Получено {total_ryabucks:,} 💵 рябаксов за {stars} ⭐{bonus_text}\n\nТекущий курс: 1 💠 = {current_rate:.2f} 💵", total_ryabucks

        except Exception as e:
            logger.error(f"Ошибка покупки рябаксов за Stars для user {user_id}: {e}")
            return False, f"Произошла ошибка: {str(e)}", 0


# Глобальный экземпляр сервиса
bank_service = BankService()
