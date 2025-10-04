# core/domain/entities.py
"""
Игровые сущности Ryabot Island
Это основные объекты игры: пользователи, специалисты, животные и т.д.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum


# ========== ВАЛЮТЫ И РЕСУРСЫ ==========

@dataclass(frozen=True)
class RBTC:
    """RBTC кристаллы - игровая валюта"""
    amount: Decimal

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("RBTC не может быть отрицательным")
        if self.amount > Decimal('21000000'):
            raise ValueError("RBTC превышает максимальный запас")


@dataclass(frozen=True)
class Energy:
    """Энергия - валюта действий"""
    current: int
    maximum: int
    last_updated: datetime

    def __post_init__(self):
        if self.current < 0 or self.current > self.maximum:
            raise ValueError("Энергия выходит за границы")


@dataclass(frozen=True)
class Resources:
    """Все ресурсы пользователя"""
    ryabucks: int = 0  # 💵 Основная валюта
    rbtc: RBTC = field(default_factory=lambda: RBTC(Decimal('0')))  # 💠 P2E валюта
    energy: Energy = field(default_factory=lambda: Energy(30, 30, datetime.now()))  # ⚡ Энергия
    liquid_experience: int = 0  # 🧪 Жидкий опыт
    golden_shards: int = 0  # ✨ Осколки золотых яиц
    golden_keys: int = 0  # 🗝️ Золотые ключи
    wood: int = 0  # 🪵 Древесина
    q_points: int = 0  # 🔮 Q-очки


# ========== ТИПЫ СПЕЦИАЛИСТОВ ==========

class SpecialistType(Enum):
    WORKER = "worker"  # 🙍‍♂️ Разнорабочий
    FARMER = "farmer"  # 👩‍🌾 Фермер
    BUILDER = "builder"  # 👷 Строитель
    COOK = "cook"  # 🧑‍🍳 Повар
    FISHERMAN = "fisherman"  # 🎣 Рыбак
    FORESTER = "forester"  # 👨‍🚒 Лесник
    SCIENTIST = "scientist"  # 🧑‍🔬 Учёный
    Q_SOLDIER = "q_soldier"  # 💂 Q-Солдат
    DOCTOR = "doctor"  # 🧑‍⚕️ Доктор
    TEACHER = "teacher"  # 🧑‍🏫 Учитель


class AnimalType(Enum):
    CHICKEN = "chicken"  # 🐔 Курица
    ROOSTER = "rooster"  # 🐓 Петух
    CHICK = "chick"  # 🐥 Цыплёнок
    HORSE = "horse"  # 🐎 Лошадь


class BuildingType(Enum):
    HOUSE = "house"  # 🏠 Дом
    HENHOUSE = "henhouse"  # 🐔 Курятник
    INCUBATOR = "incubator"  # 🐣 Инкубатор
    CHICK_HOUSE = "chick_house"  # 🐥 Цыплятник
    STABLE = "stable"  # 🐎 Конюшня
    GARDEN = "garden"  # 🌾 Огород
    FORESTRY = "forestry"  # 🌲 Лесхоз
    QUANTUM_LAB = "quantum_lab"  # ⚛️ Квантовая лаборатория


# ========== ОСНОВНЫЕ СУЩНОСТИ ==========

@dataclass
class User:
    """Пользователь игры"""
    user_id: int  # Telegram ID
    username: Optional[str]  # Username в Telegram
    resources: Resources  # Все ресурсы
    level: int = 1  # Уровень игрока
    experience: int = 0  # Опыт
    quantum_pass_until: Optional[datetime] = None  # До какого времени активен Quantum Pass
    tutorial_completed: bool = False  # Пройден ли туториал
    language: str = "ru"  # Язык интерфейса
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

    # Персонаж
    character_preset: int = 1  # Пресет внешности
    equipped_items: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "head": None, "body": "туника", "feet": None
    })

    def has_quantum_pass(self) -> bool:
        """Проверка активности Quantum Pass"""
        if not self.quantum_pass_until:
            return False
        return datetime.now() < self.quantum_pass_until

    def get_energy_regen_rate(self) -> int:
        """Скорость восстановления энергии (минуты на 1 энергию)"""
        base_rate = 48  # 48 минут базовая скорость
        if self.has_quantum_pass():
            return base_rate // 2  # x2 скорость с Quantum Pass
        return base_rate

    def can_afford_ryabucks(self, cost: int) -> bool:
        """Может ли позволить себе траты в рябаксах"""
        return self.resources.ryabucks >= cost

    def can_afford_rbtc(self, cost: Decimal) -> bool:
        """Может ли позволить себе траты в RBTC"""
        return self.resources.rbtc.amount >= cost

    def get_multiplier(self, multiplier_type: str) -> float:
        """Получение мультипликатора от Quantum Pass"""
        if not self.has_quantum_pass():
            return 1.0

        from config.settings import settings
        return settings.QUANTUM_PASS_MULTIPLIERS.get(multiplier_type, 1.0)


@dataclass
class Specialist:
    """Нанятый специалист"""
    id: int
    user_id: int
    specialist_type: SpecialistType
    level: int = 1
    status: str = "idle"  # idle, working, training, injured, dead
    experience: int = 0
    hired_at: datetime = field(default_factory=datetime.now)

    # Характеристики для экспедиций
    hp: int = 0
    stamina: int = 0
    food_capacity: int = 0
    medicine_capacity: int = 0
    cargo_capacity: int = 0
    cargo_slots: int = 0
    rbtc_bonus_percent: int = 100

    def __post_init__(self):
        """Установка характеристик по типу специалиста"""
        stats = self._get_base_stats()
        for attr, value in stats.items():
            setattr(self, attr, value)

    def _get_base_stats(self) -> Dict[str, int]:
        """Базовые характеристики по типу специалиста"""
        stats_map = {
            SpecialistType.WORKER: {
                'hp': 25, 'stamina': 30, 'food_capacity': 4,
                'medicine_capacity': 2, 'cargo_capacity': 60,
                'cargo_slots': 6, 'rbtc_bonus_percent': 80
            },
            SpecialistType.FARMER: {
                'hp': 30, 'stamina': 35, 'food_capacity': 4,
                'medicine_capacity': 4, 'cargo_capacity': 20,
                'cargo_slots': 3, 'rbtc_bonus_percent': 180
            },
            SpecialistType.Q_SOLDIER: {
                'hp': 60, 'stamina': 55, 'food_capacity': 6,
                'medicine_capacity': 3, 'cargo_capacity': 40,
                'cargo_slots': 5, 'rbtc_bonus_percent': 50
            },
            SpecialistType.SCIENTIST: {
                'hp': 30, 'stamina': 30, 'food_capacity': 4,
                'medicine_capacity': 2, 'cargo_capacity': 15,
                'cargo_slots': 3, 'rbtc_bonus_percent': 120
            }
        }
        return stats_map.get(self.specialist_type, {
            'hp': 25, 'stamina': 25, 'food_capacity': 3,
            'medicine_capacity': 2, 'cargo_capacity': 20,
            'cargo_slots': 3, 'rbtc_bonus_percent': 100
        })

    def is_available_for_work(self) -> bool:
        """Доступен ли для работы"""
        return self.status in ["idle", "working"]

    def get_hire_cost(self, current_count: int = 0) -> Dict[str, int]:
        """Стоимость найма специалиста"""
        if self.specialist_type == SpecialistType.WORKER:
            # Растущая цена в рябаксах для разнорабочих
            return {"ryabucks": 30 + (5 * current_count)}

        # Стоимость других специалистов
        specialist_costs = {
            SpecialistType.FARMER: {"liquid_experience": 50, "ryabucks": 100},
            SpecialistType.BUILDER: {"liquid_experience": 50, "ryabucks": 100},
            SpecialistType.COOK: {"liquid_experience": 75, "ryabucks": 130},
            SpecialistType.FISHERMAN: {"liquid_experience": 60, "ryabucks": 110},
            SpecialistType.FORESTER: {"liquid_experience": 60, "ryabucks": 110},
            SpecialistType.SCIENTIST: {"liquid_experience": 150, "ryabucks": 200},
            SpecialistType.Q_SOLDIER: {"liquid_experience": 100, "ryabucks": 150},
            SpecialistType.DOCTOR: {"liquid_experience": 120, "ryabucks": 180},
            SpecialistType.TEACHER: {"liquid_experience": 90, "ryabucks": 140},
        }
        return specialist_costs.get(self.specialist_type, {"ryabucks": 100})


@dataclass
class Animal:
    """Животное на ферме"""
    id: int
    user_id: int
    animal_type: AnimalType

    # Индивидуальные характеристики
    egg_production: int = 1  # яиц в день
    health: int = 85  # здоровье %
    fertility: int = 0  # шанс оплодотворения %
    lifespan: int = 30  # дней жизни

    status: str = "alive"  # alive, dead, sick
    born_at: datetime = field(default_factory=datetime.now)
    last_fed: Optional[datetime] = None
    last_collected: Optional[datetime] = None

    def days_alive(self) -> int:
        """Количество дней жизни"""
        return (datetime.now() - self.born_at).days

    def is_alive(self) -> bool:
        """Жива ли животное"""
        return self.status == "alive" and self.days_alive() < self.lifespan

    def needs_feeding(self) -> bool:
        """Нужно ли кормить"""
        if not self.last_fed:
            return True
        return datetime.now() - self.last_fed > timedelta(days=1)

    def can_produce_eggs(self) -> bool:
        """Может ли нести яйца"""
        return (self.animal_type == AnimalType.CHICKEN and
                self.is_alive() and
                not self.needs_feeding())

    def get_golden_egg_chance(self, has_quantum_pass: bool = False) -> float:
        """Шанс золотого яйца"""
        base_chance = 0.0005  # 0.05%
        if has_quantum_pass:
            return base_chance * 10  # x10 шанс с Quantum Pass
        return base_chance


@dataclass
class Building:
    """Постройка на участке"""
    id: int
    user_id: int
    building_type: BuildingType
    level: int = 1
    capacity: int = 0
    occupied_space: int = 0

    built_at: datetime = field(default_factory=datetime.now)
    construction_completed: bool = True
    construction_time_left: int = 0  # секунд

    # Позиция на участке
    plot_id: Optional[int] = None
    position_x: float = 0.0
    position_y: float = 0.0

    def __post_init__(self):
        """Установка параметров по типу постройки"""
        specs = self._get_building_specs()
        self.capacity = specs["capacity"]

    def _get_building_specs(self) -> Dict[str, Any]:
        """Характеристики построек"""
        specs = {
            BuildingType.HOUSE: {"capacity": 3, "area": 0.2},
            BuildingType.HENHOUSE: {"capacity": 25, "area": 1.0},
            BuildingType.INCUBATOR: {"capacity": 50, "area": 0.5},
            BuildingType.CHICK_HOUSE: {"capacity": 30, "area": 0.8},
            BuildingType.STABLE: {"capacity": 3, "area": 2.0},
            BuildingType.GARDEN: {"capacity": 0, "area": 0.5},
            BuildingType.FORESTRY: {"capacity": 0, "area": 2.0},
            BuildingType.QUANTUM_LAB: {"capacity": 0, "area": 3.0},
        }
        return specs.get(self.building_type, {"capacity": 10, "area": 1.0})

    def can_house_animal(self, animal_type: AnimalType) -> bool:
        """Может ли разместить животное"""
        if self.occupied_space >= self.capacity:
            return False

        # Соответствие зданий и животных
        housing_map = {
            BuildingType.HENHOUSE: [AnimalType.CHICKEN, AnimalType.ROOSTER],
            BuildingType.CHICK_HOUSE: [AnimalType.CHICK],
            BuildingType.STABLE: [AnimalType.HORSE]
        }

        allowed_animals = housing_map.get(self.building_type, [])
        return animal_type in allowed_animals

    def get_construction_cost(self) -> Dict[str, int]:
        """Стоимость постройки"""
        costs = {
            BuildingType.HOUSE: {"ryabucks": 150, "wood": 20, "liquid_experience": 15},
            BuildingType.HENHOUSE: {"ryabucks": 200, "wood": 30, "liquid_experience": 20},
            BuildingType.INCUBATOR: {"ryabucks": 250, "wood": 25, "liquid_experience": 30},
            BuildingType.CHICK_HOUSE: {"ryabucks": 180, "wood": 20, "liquid_experience": 25},
            BuildingType.STABLE: {"ryabucks": 600, "wood": 100, "liquid_experience": 40},
            BuildingType.GARDEN: {"ryabucks": 50, "wood": 10, "liquid_experience": 5},
            BuildingType.FORESTRY: {"ryabucks": 300, "wood": 10, "liquid_experience": 25},
            BuildingType.QUANTUM_LAB: {"ryabucks": 2000, "wood": 200, "liquid_experience": 100},
        }
        return costs.get(self.building_type, {"ryabucks": 100})


@dataclass
class UserStats:
    """Статистика пользователя для системы заданий"""
    user_id: int

    # Статистика фермы
    chickens_bought: int = 0
    chickens_hatched: int = 0
    chickens_raised: int = 0
    eggs_collected: int = 0
    golden_eggs_found: int = 0
    roosters_bought: int = 0
    animals_fed: int = 0

    # Статистика строительства
    buildings_built: int = 0
    henhouses_built: int = 0
    houses_built: int = 0
    upgrades_completed: int = 0
    stables_built: int = 0
    gardens_planted: int = 0

    # Статистика специалистов
    specialists_hired: int = 0
    work_tasks_completed: int = 0
    training_sessions_completed: int = 0
    laborers_hired: int = 0

    # Статистика экспедиций
    expeditions_completed: int = 0
    expeditions_failed: int = 0
    territories_explored: int = 0
    enemies_defeated: int = 0
    rbtc_found: Decimal = field(default_factory=lambda: Decimal('0'))

    # Статистика экономики
    rbtc_earned: Decimal = field(default_factory=lambda: Decimal('0'))
    rbtc_spent: Decimal = field(default_factory=lambda: Decimal('0'))
    ryabaks_earned: int = 0
    ryabaks_spent: int = 0
    items_bought: int = 0
    items_sold: int = 0
    eggs_sold: int = 0

    # Статистика земли
    land_plots_bought: int = 0
    total_area_owned: float = 0.0

    # Социальная статистика
    referrals_invited: int = 0
    daily_logins: int = 0
    achievements_unlocked: int = 0

    last_updated: datetime = field(default_factory=datetime.now)


# ========== СОБЫТИЯ ==========

@dataclass
class DomainEvent:
    """Базовое событие в игре"""
    event_id: str
    user_id: int
    event_type: str
    payload: Dict[str, Any]
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass
class SpecialistHiredEvent:
    """Событие найма специалиста"""
    # СНАЧАЛА все поля БЕЗ значений по умолчанию
    event_id: str
    user_id: int
    specialist_id: int
    specialist_type: SpecialistType
    cost: Dict[str, int]
    # ПОТОМ поля с значениями по умолчанию
    event_type: str = "specialist_hired"
    payload: Dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.payload = {
            "specialist_id": self.specialist_id,
            "specialist_type": self.specialist_type.value,
            "cost": self.cost
        }


@dataclass
class AnimalBoughtEvent:
    """Событие покупки животного"""
    # СНАЧАЛА все поля БЕЗ значений по умолчанию
    event_id: str
    user_id: int
    animal_id: int
    animal_type: AnimalType
    cost: int
    # ПОТОМ поля с значениями по умолчанию
    event_type: str = "animal_bought"
    payload: Dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.payload = {
            "animal_id": self.animal_id,
            "animal_type": self.animal_type.value,
            "cost": self.cost
        }
