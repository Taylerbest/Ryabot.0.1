# core/domain/entities.py
"""
Доменные сущности игры - переработанные под новый туториал
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

class TutorialStep(Enum):
    """Шаги туториала"""
    NOT_STARTED = "not_started"
    CHARACTER_CREATION = "character_creation"  # Создание персонажа
    SHIPWRECK = "shipwreck"                   # Кораблекрушение
    TAVERN_VISIT = "tavern_visit"            # Посещение таверны
    PAWN_SHOP = "pawn_shop"                  # Ломбард - продажа осколка
    TOWN_HALL_REGISTER = "town_hall_register" # Регистрация в ратуше
    EMPLOYER_LICENSE = "employer_license"     # Покупка лицензии работодателя
    ACADEMY_HIRE = "academy_hire"            # Найм рабочего в академии
    WORK_TASK = "work_task"                  # Выполнение работы
    CITIZEN_QUEST = "citizen_quest"          # Получение опыта у жителя
    TRAIN_SPECIALIST = "train_specialist"    # Обучение специалиста
    FARM_LICENSE = "farm_license"            # Покупка фермерской лицензии
    BUY_LAND = "buy_land"                    # Покупка земли
    BUILD_CROP_BED = "build_crop_bed"        # Постройка грядки
    PLANT_GRAIN = "plant_grain"              # Посадка зерна
    BUILD_HENHOUSE = "build_henhouse"        # Постройка курятника
    BUY_CHICKEN = "buy_chicken"              # Покупка курицы
    COMPLETED = "completed"                  # Туториал завершен

class CharacterPreset(Enum):
    """Персонажи для выбора"""
    PRESET_1 = 1   # Молодой авантюрист
    PRESET_2 = 2   # Пожилой мудрец
    PRESET_3 = 3   # Женщина-исследователь
    PRESET_4 = 4   # Крепкий моряк
    PRESET_5 = 5   # Ловкий торговец
    PRESET_6 = 6   # Таинственный странник
    PRESET_7 = 7   # Юная мечтательница
    PRESET_8 = 8   # Бородатый ремесленник
    PRESET_9 = 9   # Элегантная дама
    PRESET_10 = 10 # Суровый воин

@dataclass
class RBTC:
    """RBTC криптовалюта"""
    amount: Decimal = field(default_factory=lambda: Decimal('0.0000'))
    
    def __add__(self, other):
        if isinstance(other, RBTC):
            return RBTC(self.amount + other.amount)
        return RBTC(self.amount + Decimal(str(other)))
    
    def __sub__(self, other):
        if isinstance(other, RBTC):
            return RBTC(max(Decimal('0'), self.amount - other.amount))
        return RBTC(max(Decimal('0'), self.amount - Decimal(str(other))))

@dataclass
class Energy:
    """Энергия пользователя"""
    current: int = 30
    maximum: int = 30
    last_updated: datetime = field(default_factory=datetime.now)
    
    def regenerate(self, regen_rate_minutes: int = 15) -> 'Energy':
        """Восстановление энергии по времени"""
        now = datetime.now()
        time_diff_minutes = (now - self.last_updated).total_seconds() / 60
        energy_restored = int(time_diff_minutes // regen_rate_minutes)
        
        if energy_restored > 0:
            self.current = min(self.current + energy_restored, self.maximum)
            self.last_updated = now
        
        return self

@dataclass
class Resources:
    """Ресурсы пользователя"""
    ryabucks: int = 0                    # Начинаем с 0, получим из осколка
    rbtc: RBTC = field(default_factory=RBTC)
    energy: Energy = field(default_factory=Energy)
    liquid_experience: int = 0
    golden_shards: int = 1               # Начинаем с 1 осколка!
    golden_keys: int = 0
    wood: int = 0
    q_points: int = 0

@dataclass 
class User:
    """Пользователь игры"""
    user_id: int
    username: Optional[str] = None
    resources: Resources = field(default_factory=Resources)
    level: int = 1
    experience: int = 0
    
    # Статус туториала
    tutorial_step: TutorialStep = TutorialStep.NOT_STARTED
    tutorial_completed: bool = False
    
    # Персонаж
    character_preset: CharacterPreset = CharacterPreset.PRESET_1
    equipped_items: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "head": None,
        "body": "туника", 
        "feet": None  # босиком
    })
    
    # Лицензии
    has_employer_license: bool = False
    has_farm_license: bool = False
    
    # Quantum Pass
    quantum_pass_until: Optional[datetime] = None
    
    # Мета
    language: str = "ru"  # Только русский
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    
    def has_quantum_pass(self) -> bool:
        """Проверка активности Quantum Pass"""
        return (self.quantum_pass_until is not None and 
                self.quantum_pass_until > datetime.now())
    
    def get_energy_regen_rate(self) -> int:
        """Скорость восстановления энергии (минуты на 1 единицу)"""
        base_rate = 15  # 15 минут на 1 энергию
        if self.has_quantum_pass():
            return base_rate // 2  # x2 скорость с Quantum Pass
        return base_rate
    
    def can_work(self, energy_cost: int = 5) -> bool:
        """Проверка возможности работать"""
        current_energy = self.resources.energy.regenerate(self.get_energy_regen_rate())
        return current_energy.current >= energy_cost

@dataclass
class Specialist:
    """Нанятый специалист"""
    id: Optional[int] = None
    user_id: int = 0
    specialist_type: str = "worker"  # worker, farmer, builder, fisherman, forester
    level: int = 1
    experience: int = 0
    status: str = "idle"  # idle, working, training, injured, dead
    hired_at: datetime = field(default_factory=datetime.now)
    
    # Характеристики для экспедиций
    hp: int = 25
    stamina: int = 25
    food_capacity: int = 3
    medicine_capacity: int = 2
    cargo_capacity: int = 20
    cargo_slots: int = 3
    rbtc_bonus_percent: int = 100

@dataclass
class WorkTask:
    """Рабочая задача"""
    task_id: str
    title: str
    description: str
    energy_cost: int
    ryabucks_reward: int
    experience_reward: int
    rbtc_reward: Decimal = Decimal('0')
    requirements: Dict[str, Any] = field(default_factory=dict)  # specialist_type, level, etc
    location: str = "sea"  # sea, farm, construction, forest, anomaly, expedition

@dataclass
class Building:
    """Постройка"""
    id: Optional[int] = None
    user_id: int = 0
    building_type: str = "henhouse"
    level: int = 1
    capacity: int = 0
    occupied_space: int = 0
    
    # Строительство
    built_at: datetime = field(default_factory=datetime.now)
    construction_completed: bool = True
    construction_time_left: int = 0  # секунды
    
    # Позиция на участке
    plot_id: Optional[int] = None
    position_x: Decimal = Decimal('0.0')
    position_y: Decimal = Decimal('0.0')

@dataclass
class Animal:
    """Животное на ферме"""
    id: Optional[int] = None
    user_id: int = 0
    animal_type: str = "chicken"  # chicken, rooster, horse
    
    # Характеристики
    egg_production: int = 1
    health: int = 85
    fertility: int = 0
    lifespan: int = 30
    
    # Статус
    status: str = "alive"  # alive, dead, sick
    born_at: datetime = field(default_factory=datetime.now)
    last_fed: Optional[datetime] = None
    last_collected: Optional[datetime] = None

@dataclass
class LandPlot:
    """Участок земли"""
    plot_id: int
    owner_id: Optional[int] = None
    zone_type: str = "plains"  # plains, forest, mountains, coast, anomaly
    zone_bonus: Dict[str, int] = field(default_factory=dict)
    price_rbtc: int = 0
    price_ryabucks: int = 1000  # Базовая цена участка
    status: str = "available"  # undiscovered, available, owned, for_sale

@dataclass
class UserStats:
    """Статистика пользователя"""
    user_id: int
    
    # Животноводство
    chickens_bought: int = 0
    chickens_hatched: int = 0
    chickens_raised: int = 0
    eggs_collected: int = 0
    golden_eggs_found: int = 0
    roosters_bought: int = 0
    animals_fed: int = 0
    
    # Строительство
    buildings_built: int = 0
    henhouses_built: int = 0
    houses_built: int = 0
    upgrades_completed: int = 0
    stables_built: int = 0
    gardens_planted: int = 0
    
    # Наём и обучение
    specialists_hired: int = 0
    work_tasks_completed: int = 0
    training_sessions_completed: int = 0
    laborers_hired: int = 0
    
    # Экспедиции
    expeditions_completed: int = 0
    expeditions_failed: int = 0
    territories_explored: int = 0
    enemies_defeated: int = 0
    
    # Экономика
    rbtc_found: Decimal = field(default_factory=lambda: Decimal('0'))
    rbtc_earned: Decimal = field(default_factory=lambda: Decimal('0'))
    rbtc_spent: Decimal = field(default_factory=lambda: Decimal('0'))
    ryabucks_earned: int = 0
    ryabucks_spent: int = 0
    items_bought: int = 0
    items_sold: int = 0
    eggs_sold: int = 0
    
    # Земля
    land_plots_bought: int = 0
    total_area_owned: int = 0
    
    # Социальное
    referrals_invited: int = 0
    daily_logins: int = 0
    achievements_unlocked: int = 0

@dataclass
class AuditLogEntry:
    """Запись в аудит-логе для блокчейна"""
    id: Optional[int] = None
    user_id: int = 0
    action_type: str = "USER_ACTION"
    payload: Dict[str, Any] = field(default_factory=dict)
    hash: str = ""
    prev_hash: str = ""
    significance: int = 0  # 0-обычное, 1-важное, 2-эпическое, 3-легендарное
    tg_message_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)