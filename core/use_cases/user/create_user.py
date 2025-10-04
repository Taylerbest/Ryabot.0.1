# core/use_cases/user/create_user.py
"""
Use case для создания нового пользователя
Включает инициализацию всех начальных данных
"""

import logging
from datetime import datetime
from decimal import Decimal

from core.domain.entities import User, Resources, RBTC, Energy
from core.ports.repositories import UserRepository
from config.settings import settings

logger = logging.getLogger(__name__)

class CreateUserUseCase:
    """Use case для создания нового пользователя"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def execute(self, user_id: int, username: str = None) -> User:
        """
        Создание нового пользователя
        
        Args:
            user_id: Telegram ID пользователя
            username: Username в Telegram (опционально)
            
        Returns:
            User: Созданный или существующий пользователь
        """
        try:
            # Сначала проверяем, не существует ли уже пользователь
            existing_user = await self.user_repo.get_by_id(user_id)
            if existing_user:
                logger.info(f"👤 Пользователь {user_id} уже существует")
                # Обновляем время последней активности
                await self.user_repo.update_resources(user_id, {})
                return existing_user
            
            # Создаем нового пользователя с начальными ресурсами
            user = User(
                user_id=user_id,
                username=username,
                resources=Resources(
                    ryabucks=settings.INITIAL_RYABUCKS,  # 100 рябаксов
                    rbtc=RBTC(Decimal('0')),            # 0 RBTC
                    energy=Energy(
                        current=settings.INITIAL_ENERGY,     # 30 энергии
                        maximum=settings.INITIAL_ENERGY_MAX, # максимум 30
                        last_updated=datetime.now()
                    ),
                    liquid_experience=0,    # 0 жидкого опыта
                    golden_shards=0,        # 0 осколков золотых яиц
                    golden_keys=0,          # 0 золотых ключей
                    wood=0,                 # 0 древесины
                    q_points=0              # 0 Q-очков
                ),
                level=1,                    # 1-й уровень
                experience=0,               # 0 опыта
                quantum_pass_until=None,    # Нет Quantum Pass
                tutorial_completed=False,   # Туториал не пройден
                language="ru",              # Русский язык по умолчанию
                character_preset=1,         # Базовый персонаж
                equipped_items={
                    "head": None,
                    "body": "туника",
                    "feet": None
                }
            )
            
            # Сохраняем в БД
            created_user = await self.user_repo.create(user)
            
            # Логируем успешное создание
            logger.info(f"✅ Создан новый пользователь {user_id} (@{username})")
            
            return created_user
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания пользователя {user_id}: {e}")
            raise

class GetUserProfileUseCase:
    """Use case для получения профиля пользователя"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def execute(self, user_id: int) -> dict:
        """
        Получение профиля пользователя со всеми данными
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            dict: Данные профиля пользователя
        """
        try:
            # Получаем пользователя
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError(f"Пользователь {user_id} не найден")
            
            # Получаем статистику
            stats = await self.user_repo.get_user_stats(user_id)
            
            # Рассчитываем текущую энергию (с учетом восстановления)
            current_energy = self._calculate_current_energy(user)
            
            # Формируем профиль
            profile = {
                "user_id": user.user_id,
                "username": user.username,
                "level": user.level,
                "experience": user.experience,
                
                # Ресурсы
                "ryabucks": user.resources.ryabucks,
                "rbtc": float(user.resources.rbtc.amount),
                "energy": current_energy,
                "energy_max": user.resources.energy.maximum,
                "liquid_experience": user.resources.liquid_experience,
                "golden_shards": user.resources.golden_shards,
                "golden_keys": user.resources.golden_keys,
                "wood": user.resources.wood,
                "q_points": user.resources.q_points,
                
                # Quantum Pass
                "has_quantum_pass": user.has_quantum_pass(),
                "quantum_pass_until": user.quantum_pass_until.isoformat() if user.quantum_pass_until else None,
                
                # Персонаж
                "character_preset": user.character_preset,
                "equipped_items": user.equipped_items,
                
                # Статистика (основная)
                "chickens_bought": stats.chickens_bought,
                "eggs_collected": stats.eggs_collected,
                "golden_eggs_found": stats.golden_eggs_found,
                "specialists_hired": stats.specialists_hired,
                "buildings_built": stats.buildings_built,
                "expeditions_completed": stats.expeditions_completed,
                "land_plots_bought": stats.land_plots_bought,
                
                # Мета-данные
                "tutorial_completed": user.tutorial_completed,
                "language": user.language,
                "created_at": user.created_at.isoformat(),
                "last_active": user.last_active.isoformat()
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения профиля пользователя {user_id}: {e}")
            raise

    def _calculate_current_energy(self, user: User) -> int:
        """Рассчитать текущую энергию с учетом восстановления"""
        from datetime import timezone

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        last_updated = user.resources.energy.last_updated

        # Убираем timezone для сравнения
        if hasattr(last_updated, 'tzinfo') and last_updated.tzinfo is not None:
            last_updated = last_updated.replace(tzinfo=None)

        # Сколько времени прошло с последнего обновления
        time_diff = (now - last_updated).total_seconds()

        # Сколько энергии восстановилось
        regen_rate_seconds = user.get_energy_regen_rate() * 60  # минуты в секунды
        energy_restored = int(time_diff // regen_rate_seconds)

        # Текущая энергия (не больше максимума)
        current_energy = min(
            user.resources.energy.current + energy_restored,
            user.resources.energy.maximum
        )

        return current_energy


class UpdateUserResourcesUseCase:
    """Use case для обновления ресурсов пользователя"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def execute(self, user_id: int, resource_updates: dict) -> bool:
        """
        Обновление ресурсов пользователя
        
        Args:
            user_id: Telegram ID пользователя
            resource_updates: Словарь с обновлениями ресурсов
            
        Returns:
            bool: Успешность операции
        """
        try:
            # Проверяем существование пользователя
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError(f"Пользователь {user_id} не найден")
            
            # Валидируем обновления
            valid_resources = [
                'ryabucks', 'rbtc', 'energy', 'liquid_experience',
                'golden_shards', 'golden_keys', 'wood', 'q_points'
            ]
            
            filtered_updates = {
                key: value for key, value in resource_updates.items()
                if key in valid_resources
            }
            
            if not filtered_updates:
                logger.warning(f"⚠️ Нет валидных обновлений ресурсов для пользователя {user_id}")
                return True
            
            # Проверяем лимиты
            if 'ryabucks' in filtered_updates and filtered_updates['ryabucks'] < 0:
                filtered_updates['ryabucks'] = 0
            
            if 'energy' in filtered_updates:
                energy_max = user.resources.energy.maximum
                filtered_updates['energy'] = max(0, min(filtered_updates['energy'], energy_max))
            
            # Обновляем в БД
            success = await self.user_repo.update_resources(user_id, filtered_updates)
            
            if success:
                logger.info(f"✅ Обновлены ресурсы пользователя {user_id}: {filtered_updates}")
            else:
                logger.error(f"❌ Не удалось обновить ресурсы пользователя {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления ресурсов пользователя {user_id}: {e}")
            return False

class SpendEnergyUseCase:
    """Use case для траты энергии"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def execute(self, user_id: int, energy_cost: int) -> tuple[bool, str]:
        """
        Потратить энергию пользователя
        
        Args:
            user_id: Telegram ID пользователя  
            energy_cost: Количество энергии для траты
            
        Returns:
            tuple[bool, str]: (успех, сообщение)
        """
        try:
            # Получаем пользователя
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                return False, "Пользователь не найден"
            
            # Рассчитываем текущую энергию
            profile_uc = GetUserProfileUseCase(self.user_repo)
            profile = await profile_uc.execute(user_id)
            current_energy = profile['energy']
            
            # Проверяем достаточность энергии
            if current_energy < energy_cost:
                return False, f"⚡ Недостаточно энергии! Нужно: {energy_cost}, есть: {current_energy}"
            
            # Списываем энергию
            new_energy = current_energy - energy_cost
            success = await self.user_repo.update_resources(user_id, {"energy": new_energy})
            
            if success:
                return True, f"⚡ Потрачено {energy_cost} энергии"
            else:
                return False, "Ошибка списания энергии"
            
        except Exception as e:
            logger.error(f"❌ Ошибка траты энергии для пользователя {user_id}: {e}")
            return False, "Ошибка траты энергии"