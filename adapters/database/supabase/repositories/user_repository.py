# adapters/database/supabase/repositories/user_repository.py
"""
Репозиторий для работы с пользователями через Supabase
Реализует интерфейс UserRepository
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List

from core.domain.entities import User, Resources, RBTC, Energy, UserStats
from core.ports.repositories import UserRepository
from adapters.database.supabase.client import SupabaseClient

logger = logging.getLogger(__name__)

class SupabaseUserRepository(UserRepository):
    """Реализация UserRepository для Supabase"""
    
    def __init__(self, client: SupabaseClient):
        self.client = client
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        try:
            # Получаем данные пользователя
            user_data = await self.client.execute_query(
                table="users",
                operation="select",
                filters={"user_id": user_id},
                single=True
            )
            
            if not user_data:
                return None
            
            # Создаем объект Resources
            resources = Resources(
                ryabucks=user_data.get('ryabucks', 100),
                rbtc=RBTC(Decimal(str(user_data.get('rbtc', '0.0000')))),
                energy=Energy(
                    current=user_data.get('energy', 30),
                    maximum=user_data.get('energy_max', 30),
                    last_updated=datetime.fromisoformat(
                        user_data.get('energy_updated_at', datetime.now().isoformat())
                    ) if user_data.get('energy_updated_at') else datetime.now()
                ),
                liquid_experience=user_data.get('liquid_experience', 0),
                golden_shards=user_data.get('golden_shards', 1),
                golden_keys=user_data.get('golden_keys', 0),
                wood=user_data.get('wood', 0),
                q_points=user_data.get('q_points', 0)
            )
            
            # Создаем объект User
            user = User(
                user_id=user_data['user_id'],
                username=user_data.get('username'),
                resources=resources,
                level=user_data.get('level', 1),
                experience=user_data.get('experience', 0),
                quantum_pass_until=datetime.fromisoformat(user_data['quantum_pass_until']) 
                    if user_data.get('quantum_pass_until') else None,
                tutorial_completed=user_data.get('tutorial_completed', False),
                language=user_data.get('language', 'ru'),
                created_at=datetime.fromisoformat(user_data.get('created_at', datetime.now().isoformat())),
                last_active=datetime.fromisoformat(user_data.get('last_active', datetime.now().isoformat())),
                character_preset=user_data.get('character_preset', 1),
                equipped_items=user_data.get('equipped_items', {
                    "head": None, "body": "туника", "feet": None
                })
            )
            
            return user
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователя {user_id}: {e}")
            return None
    
    async def create(self, user: User) -> User:
        """Создать нового пользователя"""
        try:
            user_data = {
                "user_id": user.user_id,
                "username": user.username,
                "ryabucks": user.resources.ryabucks,
                "rbtc": float(user.resources.rbtc.amount),
                "energy": user.resources.energy.current,
                "energy_max": user.resources.energy.maximum,
                "energy_updated_at": user.resources.energy.last_updated.isoformat(),
                "liquid_experience": user.resources.liquid_experience,
                "golden_shards": user.resources.golden_shards,
                "golden_keys": user.resources.golden_keys,
                "wood": user.resources.wood,
                "q_points": user.resources.q_points,
                "level": user.level,
                "experience": user.experience,
                "quantum_pass_until": user.quantum_pass_until.isoformat() 
                    if user.quantum_pass_until else None,
                "tutorial_completed": user.tutorial_completed,
                "language": user.language,
                "character_preset": user.character_preset,
                "equipped_items": user.equipped_items,
                "created_at": user.created_at.isoformat(),
                "last_active": user.last_active.isoformat()
            }
            
            result = await self.client.execute_query(
                table="users",
                operation="insert",
                data=user_data,
                single=True
            )
            
            if result:
                # Инициализируем статистику пользователя
                await self._init_user_stats(user.user_id)
                logger.info(f"✅ Создан пользователь {user.user_id}")
                return user
            
            raise Exception("Не удалось создать пользователя")
            
        except Exception as e:
            logger.error(f"Ошибка создания пользователя {user.user_id}: {e}")
            raise
    
    async def update_resources(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Обновить ресурсы пользователя"""
        try:
            # Подготавливаем данные для обновления
            update_data = {}
            
            if 'ryabucks' in updates:
                update_data['ryabucks'] = updates['ryabucks']
            
            if 'rbtc' in updates:
                update_data['rbtc'] = float(updates['rbtc'])
            
            if 'energy' in updates:
                update_data['energy'] = updates['energy']
                update_data['energy_updated_at'] = datetime.now().isoformat()
            
            if 'liquid_experience' in updates:
                update_data['liquid_experience'] = updates['liquid_experience']
            
            if 'golden_shards' in updates:
                update_data['golden_shards'] = updates['golden_shards']
            
            if 'golden_keys' in updates:
                update_data['golden_keys'] = updates['golden_keys']
            
            if 'wood' in updates:
                update_data['wood'] = updates['wood']
            
            if 'q_points' in updates:
                update_data['q_points'] = updates['q_points']
            
            # Обновляем время активности
            update_data['last_active'] = datetime.now().isoformat()
            
            result = await self.client.execute_query(
                table="users",
                operation="update",
                data=update_data,
                filters={"user_id": user_id}
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Ошибка обновления ресурсов пользователя {user_id}: {e}")
            return False
    
    async def update_quantum_pass(self, user_id: int, expires_at: datetime) -> bool:
        """Обновить Quantum Pass"""
        try:
            result = await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "quantum_pass_until": expires_at.isoformat(),
                    "last_active": datetime.now().isoformat()
                },
                filters={"user_id": user_id}
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Ошибка обновления Quantum Pass для пользователя {user_id}: {e}")
            return False
    
    async def increment_stat(self, user_id: int, stat_name: str, amount: int = 1) -> bool:
        """Увеличить статистику пользователя"""
        try:
            # Сначала пытаемся получить текущее значение
            current_stat = await self.client.execute_query(
                table="user_stats",
                operation="select",
                filters={"user_id": user_id, "stat_name": stat_name},
                single=True
            )
            
            if current_stat:
                # Обновляем существующую статистику
                new_value = current_stat['stat_value'] + amount
                result = await self.client.execute_query(
                    table="user_stats",
                    operation="update",
                    data={
                        "stat_value": new_value,
                        "updated_at": datetime.now().isoformat()
                    },
                    filters={"user_id": user_id, "stat_name": stat_name}
                )
            else:
                # Создаем новую запись статистики
                result = await self.client.execute_query(
                    table="user_stats",
                    operation="insert",
                    data={
                        "user_id": user_id,
                        "stat_name": stat_name,
                        "stat_value": amount,
                        "updated_at": datetime.now().isoformat()
                    }
                )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Ошибка обновления статистики {stat_name} для пользователя {user_id}: {e}")
            return False
    
    async def get_user_stats(self, user_id: int) -> UserStats:
        """Получить статистику пользователя"""
        try:
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
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики для пользователя {user_id}: {e}")
            return UserStats(user_id=user_id)
    
    async def _init_user_stats(self, user_id: int):
        """Инициализация статистики для нового пользователя"""
        try:
            # Создаем базовые записи статистики
            base_stats = [
                "chickens_bought", "chickens_hatched", "chickens_raised",
                "eggs_collected", "golden_eggs_found", "roosters_bought", "animals_fed",
                "buildings_built", "henhouses_built", "houses_built",
                "upgrades_completed", "stables_built", "gardens_planted", 
                "specialists_hired", "work_tasks_completed", "training_sessions_completed",
                "laborers_hired", "expeditions_completed", "expeditions_failed",
                "territories_explored", "enemies_defeated", "rbtc_found",
                "rbtc_earned", "rbtc_spent", "ryabaks_earned", "ryabaks_spent",
                "items_bought", "items_sold", "eggs_sold", "land_plots_bought",
                "total_area_owned", "referrals_invited", "daily_logins",
                "achievements_unlocked"
            ]
            
            stats_data = []
            for stat_name in base_stats:
                stats_data.append({
                    "user_id": user_id,
                    "stat_name": stat_name,
                    "stat_value": 0,
                    "updated_at": datetime.now().isoformat()
                })
            
            await self.client.execute_query(
                table="user_stats",
                operation="insert",
                data=stats_data
            )
            
            logger.info(f"✅ Инициализирована статистика для пользователя {user_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации статистики для пользователя {user_id}: {e}")
            # Не критическая ошибка, продолжаем работу
    
    async def update_last_active(self, user_id: int) -> bool:
        """Обновить время последней активности"""
        try:
            result = await self.client.execute_query(
                table="users",
                operation="update",
                data={"last_active": datetime.now().isoformat()},
                filters={"user_id": user_id}
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Ошибка обновления времени активности для пользователя {user_id}: {e}")
            return False
    
    async def get_active_user_ids(self, days: int = 30, limit: Optional[int] = None) -> List[int]:
        """Получить ID активных пользователей"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["user_id"],
                filters={"last_active": {"gte": cutoff_date.isoformat()}},
                limit=limit
            )
            
            return [row['user_id'] for row in result]
            
        except Exception as e:
            logger.error(f"Ошибка получения активных пользователей: {e}")
            return []