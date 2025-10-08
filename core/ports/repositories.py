# core/ports/repositories.py
"""
Порты (интерфейсы) репозиториев для Ryabot Island
Адаптеры Supabase/PostgreSQL
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime

from core.domain.entities import User, Specialist, Animal, Building, UserStats


class UserRepository(ABC):
    """Репозиторий пользователей"""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        pass

    @abstractmethod
    async def create(self, user: User) -> User:
        """Создать пользователя"""
        pass

    @abstractmethod
    async def update_resources(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Обновить ресурсы пользователя"""
        pass

    @abstractmethod
    async def update_quantum_pass(self, user_id: int, expires_at: datetime) -> bool:
        """Обновить Quantum Pass"""
        pass

    @abstractmethod
    async def increment_stat(self, user_id: int, stat_name: str, amount: int = 1) -> bool:
        """Увеличить статистику"""
        pass

    @abstractmethod
    async def get_user_stats(self, user_id: int) -> UserStats:
        """Получить статистику пользователя"""
        pass

    @abstractmethod
    async def update_display_name(self, user_id: int, display_name: str) -> bool:
        """Обновить игровое имя пользователя"""
        pass

    @abstractmethod
    async def check_display_name_exists(self, display_name: str) -> bool:
        """Проверить существование игрового имени"""
        pass


class SpecialistRepository(ABC):
    """Репозиторий специалистов"""

    @abstractmethod
    async def get_by_user(self, user_id: int) -> List[Specialist]:
        """Получить всех специалистов пользователя"""
        pass

    @abstractmethod
    async def get_by_id(self, specialist_id: int) -> Optional[Specialist]:
        """Получить специалиста по ID"""
        pass

    @abstractmethod
    async def create(self, specialist: Specialist) -> Specialist:
        """Создать специалиста"""
        pass

    @abstractmethod
    async def count_by_user_and_type(self, user_id: int, specialist_type: str) -> int:
        """Подсчитать специалистов по типу"""
        pass

    @abstractmethod
    async def count_by_user(self, user_id: int) -> int:
        """Подсчитать всех специалистов пользователя"""
        pass

    @abstractmethod
    async def count_houses(self, user_id: int) -> int:
        """Подсчитать дома пользователя"""
        pass

    @abstractmethod
    async def delete(self, specialist_id: int) -> bool:
        """Удалить специалиста"""
        pass


class AnimalRepository(ABC):
    """Репозиторий животных"""

    @abstractmethod
    async def get_by_user(self, user_id: int) -> List[Animal]:
        """Получить всех животных пользователя"""
        pass

    @abstractmethod
    async def get_by_id(self, animal_id: int) -> Optional[Animal]:
        """Получить животное по ID"""
        pass

    @abstractmethod
    async def create(self, animal: Animal) -> Animal:
        """Создать животное"""
        pass

    @abstractmethod
    async def count_by_user_and_type(self, user_id: int, animal_type: str) -> int:
        """Подсчитать животных по типу"""
        pass

    @abstractmethod
    async def update_status(self, animal_id: int, status: str) -> bool:
        """Обновить статус животного"""
        pass

    @abstractmethod
    async def update_last_fed(self, animal_id: int, fed_at: datetime) -> bool:
        """Обновить время последнего кормления"""
        pass

    @abstractmethod
    async def update_last_collected(self, animal_id: int, collected_at: datetime) -> bool:
        """Обновить время последнего сбора"""
        pass


class BuildingRepository(ABC):
    """Репозиторий зданий"""

    @abstractmethod
    async def get_by_user(self, user_id: int) -> List[Building]:
        """Получить все здания пользователя"""
        pass

    @abstractmethod
    async def create(self, building: Building) -> Building:
        """Создать здание"""
        pass

    @abstractmethod
    async def count_by_type(self, user_id: int, building_type: str) -> int:
        """Подсчитать здания по типу"""
        pass
