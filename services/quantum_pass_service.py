# services/quantum_pass_service.py
import logging
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from adapters.database.supabase.client import get_supabase_client
from config.settings import settings

logger = logging.getLogger(__name__)


class QuantumPassService:
    def __init__(self):
        self.client = None

        # Цены Quantum Pass в RBTC
        self.PRICES = {
            '1_month': 35,
            '3_months': 84,
            '6_months': 168,
            '1_year': 294
        }

        # Продолжительность в днях
        self.DURATIONS = {
            '1_month': 30,
            '3_months': 90,
            '6_months': 180,
            '1_year': 365
        }

    async def _ensure_client(self):
        if not self.client:
            self.client = await get_supabase_client()

    async def get_quantum_pass_stats(self) -> dict:
        """Получить статистику пользователей с Q-Pass"""
        try:
            await self._ensure_client()

            # ✅ ИСПРАВЛЕНО: Получаем всех пользователей и фильтруем в Python
            all_users = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id", "quantum_pass_until"]
            )

            if not all_users:
                return {'total_active_qpass_users': 0}

            # Фильтрация активных Q-Pass в Python
            now = datetime.now(timezone.utc)
            active_count = 0

            for user in all_users:
                qpass_until = user.get('quantum_pass_until')
                if qpass_until:
                    try:
                        # Парсинг даты
                        if isinstance(qpass_until, str):
                            expiry = datetime.fromisoformat(qpass_until.replace('Z', '+00:00'))
                        else:
                            expiry = qpass_until

                        # Добавляем timezone если нет
                        if expiry.tzinfo is None:
                            expiry = expiry.replace(tzinfo=timezone.utc)

                        if expiry > now:
                            active_count += 1
                    except Exception as e:
                        logger.debug(f"Ошибка парсинга даты для пользователя {user.get('user_id')}: {e}")
                        continue

            return {'total_active_qpass_users': active_count}

        except Exception as e:
            logger.error(f"Ошибка получения статистики Q-Pass: {e}")
            return {'total_active_qpass_users': 0}

    async def get_user_quantum_pass_info(self, user_id: int) -> dict:
        """Получить информацию о Q-Pass пользователя"""
        try:
            await self._ensure_client()

            user = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["quantum_pass_until", "rbtc"],
                filters={"user_id": user_id},
                single=True
            )

            if not user:
                return {
                    'has_quantum_pass': False,
                    'time_left': None,
                    'user_rbtc': 0
                }

            quantum_pass_until = user.get('quantum_pass_until')
            has_quantum_pass = False
            time_left = None

            if quantum_pass_until:
                try:
                    # ✅ ИСПРАВЛЕНО: Правильная обработка timezone
                    if isinstance(quantum_pass_until, str):
                        # Убираем 'Z' и добавляем +00:00 для правильного парсинга
                        expiry_date = datetime.fromisoformat(quantum_pass_until.replace('Z', '+00:00'))
                    else:
                        expiry_date = quantum_pass_until

                    # Убедимся что обе даты с timezone
                    if expiry_date.tzinfo is None:
                        expiry_date = expiry_date.replace(tzinfo=timezone.utc)

                    now = datetime.now(timezone.utc)

                    if expiry_date > now:
                        has_quantum_pass = True
                        time_delta = expiry_date - now

                        days = time_delta.days
                        hours, remainder = divmod(time_delta.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)

                        time_left = {
                            'days': days,
                            'hours': hours,
                            'minutes': minutes,
                            'total_seconds': time_delta.total_seconds()
                        }
                except Exception as date_error:
                    logger.error(f"Ошибка обработки даты Q-Pass: {date_error}, значение: {quantum_pass_until}")

            return {
                'has_quantum_pass': has_quantum_pass,
                'time_left': time_left,
                'user_rbtc': Decimal(str(user.get('rbtc', 0)))
            }

        except Exception as e:
            logger.error(f"Ошибка получения информации Q-Pass для пользователя {user_id}: {e}")
            return {
                'has_quantum_pass': False,
                'time_left': None,
                'user_rbtc': Decimal('0')
            }

    def format_time_left(self, time_left: dict) -> str:
        """Форматировать оставшееся время"""
        if not time_left:
            return "Не активен"

        days = time_left['days']
        hours = time_left['hours']
        minutes = time_left['minutes']

        if days > 0:
            if hours > 0:
                return f"{days} дн. {hours} ч."
            else:
                return f"{days} дн."
        elif hours > 0:
            if minutes > 0:
                return f"{hours} ч. {minutes} мин."
            else:
                return f"{hours} ч."
        else:
            return f"{minutes} мин."

    async def purchase_quantum_pass(self, user_id: int, duration_key: str) -> Tuple[bool, str]:
        """Покупка Quantum Pass"""
        try:
            await self._ensure_client()

            if duration_key not in self.PRICES:
                return False, "Неверная продолжительность подписки"

            price = self.PRICES[duration_key]
            duration_days = self.DURATIONS[duration_key]

            # Получить текущего пользователя
            user = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["rbtc", "quantum_pass_until"],
                filters={"user_id": user_id},
                single=True
            )

            if not user:
                return False, "Пользователь не найден"

            user_rbtc = Decimal(str(user.get('rbtc', 0)))

            if user_rbtc < price:
                return False, f"Недостаточно RBTC. Нужно: {price} 💠, есть: {user_rbtc:.4f} 💠"

            # ✅ ИСПРАВЛЕНО: Используем timezone-aware datetime
            current_expiry = user.get('quantum_pass_until')
            now = datetime.now(timezone.utc)

            if current_expiry:
                try:
                    if isinstance(current_expiry, str):
                        current_expiry_date = datetime.fromisoformat(current_expiry.replace('Z', '+00:00'))
                    else:
                        current_expiry_date = current_expiry

                    if current_expiry_date.tzinfo is None:
                        current_expiry_date = current_expiry_date.replace(tzinfo=timezone.utc)

                    if current_expiry_date > now:
                        # Продлить с текущей даты окончания
                        new_expiry = current_expiry_date + timedelta(days=duration_days)
                    else:
                        # Активировать с текущего момента
                        new_expiry = now + timedelta(days=duration_days)
                except Exception:
                    # Если ошибка парсинга, активируем с текущего момента
                    new_expiry = now + timedelta(days=duration_days)
            else:
                # Активировать с текущего момента
                new_expiry = now + timedelta(days=duration_days)

            # Списать RBTC (сжечь)
            new_rbtc = float(user_rbtc - price)

            # Обновить пользователя
            await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "rbtc": new_rbtc,
                    "quantum_pass_until": new_expiry.isoformat(),
                    "last_active": datetime.now(timezone.utc).isoformat()
                },
                filters={"user_id": user_id}
            )

            # Записать транзакцию в аудит (опционально)
            try:
                await self.client.execute_query(
                    table="bank_transactions",
                    operation="insert",
                    data={
                        "user_id": user_id,
                        "transaction_type": "quantum_pass_purchase",
                        "amount_from": float(price),
                        "amount_to": 0,  # Сжигание
                        "currency_from": "rbtc",
                        "currency_to": "burned",
                        "exchange_rate": 1
                    }
                )
            except Exception as audit_error:
                logger.warning(f"Не удалось записать аудит покупки Q-Pass: {audit_error}")

            duration_text = {
                '1_month': '1 месяц',
                '3_months': '3 месяца',
                '6_months': '6 месяцев',
                '1_year': '1 год'
            }.get(duration_key, duration_key)

            expiry_formatted = new_expiry.strftime("%d.%m.%Y %H:%M")

            return True, f"✅ Quantum Pass успешно {'продлен' if current_expiry else 'активирован'} на {duration_text}!\n\n💠 Списано: {price} RBTC\n⏳ Действует до: {expiry_formatted}"

        except Exception as e:
            logger.error(f"Ошибка покупки Q-Pass для пользователя {user_id}: {e}")
            return False, f"Произошла ошибка: {str(e)}"


# Глобальный экземпляр
quantum_pass_service = QuantumPassService()
