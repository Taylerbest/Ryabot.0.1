# adapters/database/supabase/repositories/user_repository.py
"""
Исправленный репозиторий для работы с пользователями через Supabase
Реализует интерфейс UserRepository с улучшенной безопасностью и производительностью
"""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
import asyncio

from core.domain.entities import User, Resources, RBTC, Energy, UserStats
from core.ports.repositories import UserRepository
from adapters.database.supabase.client import SupabaseClient

# Настройка логирования с фильтрацией чувствительных данных
logger = logging.getLogger(__name__)


# Исключения для более точной обработки ошибок
class UserRepositoryError(Exception):
    """Базовое исключение для репозитория пользователей"""
    pass


class UserNotFoundError(UserRepositoryError):
    """Пользователь не найден"""
    pass


class DatabaseTransactionError(UserRepositoryError):
    """Ошибка транзакции базы данных"""
    pass


class ValidationError(UserRepositoryError):
    """Ошибка валидации данных"""
    pass


@dataclass
class UserUpdateData:
    """Валидированные данные для обновления пользователя"""
    ryabucks: Optional[int] = None
    rbtc: Optional[Decimal] = None
    energy: Optional[int] = None
    liquid_experience: Optional[int] = None
    golden_shards: Optional[int] = None
    golden_keys: Optional[int] = None
    wood: Optional[int] = None
    q_points: Optional[int] = None

    def __post_init__(self):
        """Валидация данных после инициализации"""
        if self.ryabucks is not None and self.ryabucks < 0:
            raise ValidationError("Ryabucks не могут быть отрицательными")
        if self.rbtc is not None and self.rbtc < 0:
            raise ValidationError("RBTC не может быть отрицательным")
        if self.energy is not None and (self.energy < 0 or self.energy > 200):
            raise ValidationError("Энергия должна быть от 0 до 200")


class SupabaseUserRepository(UserRepository):
    """Исправленная реализация UserRepository для Supabase"""

    def __init__(self, client: SupabaseClient):
        self.client = client
        self._cache_ttl = 300  # 5 минут кеш
        self._user_cache: Dict[int, tuple[User, datetime]] = {}

    def _validate_user_id(self, user_id: int) -> None:
        """Валидация ID пользователя"""
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValidationError(f"Некорректный user_id: {user_id}")

    def _get_cached_user(self, user_id: int) -> Optional[User]:
        """Получение пользователя из кеша"""
        if user_id in self._user_cache:
            user, cached_at = self._user_cache[user_id]
            if datetime.now(timezone.utc) - cached_at < timedelta(seconds=self._cache_ttl):
                return user
            else:
                del self._user_cache[user_id]
        return None

    def _cache_user(self, user: User) -> None:
        """Кеширование пользователя"""
        self._user_cache[user.user_id] = (user, datetime.now(timezone.utc))

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID с кешированием и улучшенной обработкой ошибок"""
        try:
            self._validate_user_id(user_id)

            # Проверяем кеш
            cached_user = self._get_cached_user(user_id)
            if cached_user:
                return cached_user

            # Получаем данные пользователя одним запросом
            user_data = await self.client.execute_query(
                table="users",
                operation="select",
                columns=[
                    "user_id", "username", "display_name", "player_id",
                    "ryabucks", "rbtc", "energy", "energy_max", "energy_updated_at",
                    "liquid_experience", "golden_shards", "golden_keys",
                    "wood", "q_points", "level", "experience", "quantum_pass_until",
                    "tutorial_completed", "language", "created_at", "last_active",
                    "character_preset", "equipped_items"
                ],
                filters={"user_id": user_id},
                single=True
            )

            if not user_data:
                return None

            # Создаем объект Resources с валидацией
            try:
                resources = Resources(
                    ryabucks=max(0, user_data.get('ryabucks', 100)),
                    rbtc=RBTC(Decimal(str(user_data.get('rbtc', '0.0000')))),
                    energy=Energy(
                        current=max(0, min(200, user_data.get('energy', 30))),
                        maximum=max(30, min(200, user_data.get('energy_max', 30))),
                        last_updated=self._parse_datetime(
                            user_data.get('energy_updated_at')
                        )
                    ),
                    liquid_experience=max(0, user_data.get('liquid_experience', 0)),
                    golden_shards=max(0, user_data.get('golden_shards', 1)),
                    golden_keys=max(0, user_data.get('golden_keys', 0)),
                    wood=max(0, user_data.get('wood', 0)),
                    q_points=max(0, user_data.get('q_points', 0))
                )
            except (ValueError, TypeError) as e:
                logger.error(f"Ошибка создания ресурсов для пользователя {user_id}: {e}")
                raise ValidationError(f"Некорректные данные ресурсов: {e}")

            # Создаем объект User
            user = User(
                user_id=user_data['user_id'],
                username=user_data.get('username'),
                display_name=user_data.get("display_name"),
                player_id=user_data.get("player_id"),
                resources=resources,
                level=max(1, user_data.get('level', 1)),
                experience=max(0, user_data.get('experience', 0)),
                quantum_pass_until=self._parse_datetime(user_data.get('quantum_pass_until')),
                tutorial_completed=user_data.get('tutorial_completed', False),
                language=user_data.get('language', 'ru'),
                created_at=self._parse_datetime(user_data.get('created_at')) or datetime.now(timezone.utc),
                last_active=self._parse_datetime(user_data.get('last_active')) or datetime.now(timezone.utc),
                character_preset=max(1, user_data.get('character_preset', 1)),
                equipped_items=user_data.get('equipped_items', {
                    "head": None, "body": "туника", "feet": None
                })
            )

            # Кешируем пользователя
            self._cache_user(user)
            return user

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка получения пользователя {user_id}: {e}", exc_info=True)
            return None

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Безопасный парсинг datetime с timezone"""
        if not dt_str:
            return None
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            logger.warning(f"Не удалось распарсить datetime: {dt_str}")
            return None

    async def create(self, user: User) -> User:
        """Создать нового пользователя с транзакцией"""
        try:
            self._validate_user_id(user.user_id)

            # Подготавливаем данные с валидацией
            user_data = {
                "user_id": user.user_id,
                "username": user.username,
                "display_name": user.display_name,
                "player_id": user.player_id,
                "ryabucks": max(0, user.resources.ryabucks),
                "rbtc": float(max(Decimal('0'), user.resources.rbtc.amount)),
                "energy": max(0, min(200, user.resources.energy.current)),
                "energy_max": max(30, min(200, user.resources.energy.maximum)),
                "energy_updated_at": user.resources.energy.last_updated.isoformat(),
                "liquid_experience": max(0, user.resources.liquid_experience),
                "golden_shards": max(0, user.resources.golden_shards),
                "golden_keys": max(0, user.resources.golden_keys),
                "wood": max(0, user.resources.wood),
                "q_points": max(0, user.resources.q_points),
                "level": max(1, user.level),
                "experience": max(0, user.experience),
                "quantum_pass_until": user.quantum_pass_until.isoformat() if user.quantum_pass_until else None,
                "tutorial_completed": user.tutorial_completed,
                "language": user.language or 'ru',
                "character_preset": max(1, user.character_preset),
                "equipped_items": user.equipped_items or {"head": None, "body": "туника", "feet": None},
                "created_at": user.created_at.isoformat(),
                "last_active": user.last_active.isoformat()
            }

            # Используем транзакцию для создания пользователя и инициализации статистики
            async with self.client.transaction() as tx:
                # Создаем пользователя
                result = await tx.execute_query(
                    table="users",
                    operation="insert",
                    data=user_data,
                    single=True
                )

                if not result:
                    raise DatabaseTransactionError("Не удалось создать пользователя")

                # Инициализируем статистику
                await self._init_user_stats_in_transaction(tx, user.user_id)

            logger.info(f"✅ Создан пользователь {user.user_id}")
            return user

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка создания пользователя {user.user_id}: {e}", exc_info=True)
            raise DatabaseTransactionError(f"Ошибка создания пользователя: {e}")

    async def _init_user_stats_in_transaction(self, transaction, user_id: int):
        """Инициализация статистики пользователя в транзакции"""
        base_stats = [
            "chickens_bought", "chickens_hatched", "chickens_raised",
            "eggs_collected", "golden_eggs_found", "roosters_bought",
            "animals_fed", "buildings_built", "henhouses_built",
            "houses_built", "upgrades_completed", "stables_built",
            "gardens_planted", "specialists_hired", "work_tasks_completed",
            "training_sessions_completed", "laborers_hired",
            "expeditions_completed", "expeditions_failed",
            "territories_explored", "enemies_defeated", "rbtc_found",
            "rbtc_earned", "rbtc_spent", "ryabaks_earned", "ryabaks_spent",
            "items_bought", "items_sold", "eggs_sold", "land_plots_bought",
            "total_area_owned", "referrals_invited", "daily_logins",
            "achievements_unlocked"
        ]

        stats_data = [
            {
                "user_id": user_id,
                "stat_name": stat_name,
                "stat_value": 0,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            for stat_name in base_stats
        ]

        await transaction.execute_query(
            table="user_stats",
            operation="insert",
            data=stats_data
        )

    async def update_resources(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Обновить ресурсы пользователя с валидацией и оптимизацией"""
        try:
            self._validate_user_id(user_id)

            # Валидируем данные обновления
            validated_updates = UserUpdateData(**updates)

            # Подготавливаем данные для обновления
            update_data = {"last_active": datetime.now(timezone.utc).isoformat()}

            if validated_updates.ryabucks is not None:
                update_data['ryabucks'] = validated_updates.ryabucks

            if validated_updates.rbtc is not None:
                update_data['rbtc'] = float(validated_updates.rbtc)

            if validated_updates.energy is not None:
                update_data['energy'] = validated_updates.energy
                update_data['energy_updated_at'] = datetime.now(timezone.utc).isoformat()

            if validated_updates.liquid_experience is not None:
                update_data['liquid_experience'] = validated_updates.liquid_experience

            if validated_updates.golden_shards is not None:
                update_data['golden_shards'] = validated_updates.golden_shards

            if validated_updates.golden_keys is not None:
                update_data['golden_keys'] = validated_updates.golden_keys

            if validated_updates.wood is not None:
                update_data['wood'] = validated_updates.wood

            if validated_updates.q_points is not None:
                update_data['q_points'] = validated_updates.q_points

            result = await self.client.execute_query(
                table="users",
                operation="update",
                data=update_data,
                filters={"user_id": user_id}
            )

            # Очищаем кеш
            if user_id in self._user_cache:
                del self._user_cache[user_id]

            return bool(result)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка обновления ресурсов пользователя {user_id}: {e}")
            return False

    async def update_quantum_pass(self, user_id: int, expires_at: datetime) -> bool:
        """Обновить Quantum Pass с валидацией"""
        try:
            self._validate_user_id(user_id)

            if not isinstance(expires_at, datetime):
                raise ValidationError("expires_at должен быть datetime объектом")

            # Убеждаемся, что datetime имеет timezone
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            result = await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "quantum_pass_until": expires_at.isoformat(),
                    "last_active": datetime.now(timezone.utc).isoformat()
                },
                filters={"user_id": user_id}
            )

            # Очищаем кеш
            if user_id in self._user_cache:
                del self._user_cache[user_id]

            return bool(result)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка обновления Quantum Pass для пользователя {user_id}: {e}")
            return False

    async def increment_stat(self, user_id: int, stat_name: str, amount: int = 1) -> bool:
        """Увеличить статистику пользователя с оптимизацией"""
        try:
            self._validate_user_id(user_id)

            if not isinstance(stat_name, str) or not stat_name.strip():
                raise ValidationError("stat_name должен быть непустой строкой")

            if not isinstance(amount, int) or amount < 0:
                raise ValidationError("amount должен быть положительным целым числом")

            # Используем upsert для атомарного обновления
            await self.client.execute_query(
                table="user_stats",
                operation="upsert",
                data={
                    "user_id": user_id,
                    "stat_name": stat_name,
                    "stat_value": f"COALESCE(stat_value, 0) + {amount}",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                conflict_columns=["user_id", "stat_name"]
            )

            return True

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка обновления статистики {stat_name} для пользователя {user_id}: {e}")
            return False

    async def get_user_stats(self, user_id: int) -> UserStats:
        """Получить статистику пользователя с кешированием"""
        try:
            self._validate_user_id(user_id)

            stats_data = await self.client.execute_query(
                table="user_stats",
                operation="select",
                filters={"user_id": user_id}
            )

            # Создаем объект статистики с значениями по умолчанию
            stats = UserStats(user_id=user_id)

            # Заполняем значения из БД
            for stat in stats_data:
                stat_name = stat['stat_name']
                stat_value = stat['stat_value']

                if hasattr(stats, stat_name):
                    # Обрабатываем Decimal поля
                    if stat_name in ['rbtc_found', 'rbtc_earned', 'rbtc_spent']:
                        stat_value = Decimal(str(stat_value))

                    setattr(stats, stat_name, stat_value)

            return stats

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка получения статистики для пользователя {user_id}: {e}")
            return UserStats(user_id=user_id)

    async def update_last_active(self, user_id: int) -> bool:
        """Обновить время последней активности (batch операция для оптимизации)"""
        try:
            self._validate_user_id(user_id)

            result = await self.client.execute_query(
                table="users",
                operation="update",
                data={"last_active": datetime.now(timezone.utc).isoformat()},
                filters={"user_id": user_id}
            )

            return bool(result)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка обновления времени активности для пользователя {user_id}: {e}")
            return False

    async def get_active_user_ids(self, days: int = 30, limit: Optional[int] = None) -> List[int]:
        """Получить ID активных пользователей с оптимизированным запросом"""
        try:
            if days <= 0:
                raise ValidationError("days должен быть положительным числом")

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"last_active": {"gte": cutoff_date.isoformat()}},
                limit=limit or 10000  # Разумный лимит по умолчанию
            )

            return [row['user_id'] for row in result] if result else []

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка получения активных пользователей: {e}")
            return []

    async def update_display_name(self, user_id: int, display_name: str) -> bool:
        """Обновить игровое имя пользователя с валидацией"""
        try:
            self._validate_user_id(user_id)

            if not isinstance(display_name, str):
                raise ValidationError("display_name должен быть строкой")

            display_name = display_name.strip()
            if not display_name or len(display_name) > 50:
                raise ValidationError("display_name должен быть от 1 до 50 символов")

            result = await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "display_name": display_name,
                    "last_active": datetime.now(timezone.utc).isoformat()
                },
                filters={"user_id": user_id}
            )

            # Очищаем кеш
            if user_id in self._user_cache:
                del self._user_cache[user_id]

            return bool(result)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка обновления имени для {user_id}: {e}", exc_info=True)
            return False

    async def check_display_name_exists(self, display_name: str) -> bool:
        """Проверить существование игрового имени с валидацией"""
        try:
            if not isinstance(display_name, str):
                raise ValidationError("display_name должен быть строкой")

            display_name = display_name.strip()
            if not display_name:
                raise ValidationError("display_name не может быть пустым")

            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"display_name": display_name},
                limit=1
            )

            exists = bool(result and len(result) > 0)
            logger.debug(f"Проверка имени '{display_name}': exists={exists}")
            return exists

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка проверки имени {display_name}: {e}", exc_info=True)
            return False

    async def batch_update_last_active(self, user_ids: List[int]) -> int:
        """Batch обновление времени активности для оптимизации производительности"""
        try:
            if not user_ids:
                return 0

            # Валидируем все user_ids
            for user_id in user_ids:
                self._validate_user_id(user_id)

            current_time = datetime.now(timezone.utc).isoformat()

            # Используем batch операцию
            result = await self.client.execute_batch_update(
                table="users",
                updates=[
                    {
                        "data": {"last_active": current_time},
                        "filters": {"user_id": user_id}
                    }
                    for user_id in user_ids
                ]
            )

            return len(result) if result else 0

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка batch обновления активности: {e}")
            return 0

    def clear_cache(self) -> None:
        """Очистить кеш пользователей"""
        self._user_cache.clear()
        logger.info("Кеш пользователей очищен")


logger.info("✅ Fixed UserRepository loaded with enhanced security and performance")