# core/ports/repositories.py
"""
Интерфейсы репозиториев (контракты для работы с данными)
Эти интерфейсы реализуются для Supabase и PostgreSQL
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime

from core.domain.entities import User, Specialist, Animal, Building, UserStats

class UserRepository(ABC):
    """Интерфейс для работы с пользователями"""
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        pass
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """Создать нового пользователя"""
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

class SpecialistRepository(ABC):
    """Интерфейс для работы со специалистами"""
    
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
        """Создать нового специалиста"""
        pass
    
    @abstractmethod
    async def count_by_user_and_type(self, user_id: int, specialist_type: SpecialistType) -> int:
        """Подсчитать специалистов определенного типа у пользователя"""
        pass
    
    @abstractmethod
    async def count_by_user(self, user_id: int) -> int:
        """Подсчитать всех специалистов пользователя"""
        pass
    
    @abstractmethod
    async def count_houses(self, user_id: int) -> int:
        """Подсчитать количество домов пользователя"""
        pass
    
    @abstractmethod
    async def delete(self, specialist_id: int) -> bool:
        """Удалить специалиста"""
        pass

class AnimalRepository(ABC):
    """Интерфейс для работы с животными"""
    
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
        """Создать новое животное"""
        pass
    
    @abstractmethod
    async def count_by_user_and_type(self, user_id: int, animal_type: AnimalType) -> int:
        """Подсчитать животных определенного типа у пользователя"""
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
    """Интерфейс для работы с постройками"""
    
    @abstractmethod
    async def get_by_user(self, user_id: int) -> List[Building]:
        """Получить все постройки пользователя"""
        pass
    
    @abstractmethod
    async def create(self, building: Building) -> Building:
        """Создать новую постройку"""
        pass
    
    @abstractmethod
    async def count_by_type(self, user_id: int, building_type) -> int:
        """Подсчитать постройки определенного типа"""
        pass

class CacheRepository(ABC):
    """Интерфейс для кэширования"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Сохранить значение в кэш"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        pass