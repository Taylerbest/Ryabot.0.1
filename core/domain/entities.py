# core/domain/entities.py
"""
Доменные сущности для Ryabot Island - новая архитектура
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum

class TutorialStep(Enum):
    """Шаги туториала и системы заданий"""
    # Выбор языка и персонажа
    NOT_STARTED = "not_started"
    LANGUAGE_SELECTION = "language_selection"
    CHARACTER_CREATION = "character_creation"
    
    # Сюжетная линия
    SHIPWRECK = "shipwreck"                 # Кораблекрушение
    TAVERN_VISIT = "tavern_visit"           # Посещение таверны
    PAWN_SHOP = "pawn_shop"                 # Ломбард - продажа осколка
    TOWN_HALL_REGISTER = "town_hall_register"   # Регистрация в ратуше
    EMPLOYER_LICENSE = "employer_license"    # Покупка лицензии работодателя
    
    # Доступ к острову получен, но есть задания
    ISLAND_ACCESS_GRANTED = "island_access_granted"  # Игрок может входить на остров
    
    # Задания (выполняются через интерфейс)
    TASK_HIRE_WORKER = "task_hire_worker"       # Задание: нанять рабочего
    TASK_FIRST_WORK = "task_first_work"         # Задание: первая работа
    TASK_CITIZEN_QUEST = "task_citizen_quest"   # Задание: получить опыт у жителя
    TASK_TRAIN_SPECIALIST = "task_train_specialist"  # Задание: обучить специалиста
    TASK_BUY_FARM_LICENSE = "task_buy_farm_license"  # Задание: фермерская лицензия
    TASK_BUY_LAND = "task_buy_land"             # Задание: купить землю
    TASK_BUILD_CROP_BED = "task_build_crop_bed" # Задание: построить грядку
    TASK_PLANT_GRAIN = "task_plant_grain"       # Задание: посадить зерно
    TASK_BUILD_HENHOUSE = "task_build_henhouse" # Задание: построить курятник
    TASK_BUY_CHICKEN = "task_buy_chicken"       # Задание: купить курицу
    
    COMPLETED = "completed"                     # Туториал завершен

class Language(Enum):
    """Поддерживаемые языки"""
    RU = "ru"
    EN = "en"

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

class QuestStatus(Enum):
    """Статус задания"""
    LOCKED = "locked"           # Заблокировано
    AVAILABLE = "available"     # Доступно
    IN_PROGRESS = "in_progress" # В процессе
    COMPLETED = "completed"     # Завершено

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
    ryabucks: int = 0
    rbtc: RBTC = field(default_factory=RBTC)
    energy: Energy = field(default_factory=Energy)
    liquid_experience: int = 0
    golden_shards: int = 1               # Начинаем с осколка
    golden_keys: int = 0
    wood: int = 0
    stone: int = 0
    grain: int = 0
    q_points: int = 0

@dataclass
class Quest:
    """Задание в системе заданий"""
    quest_id: str
    title: str
    description: str
    status: QuestStatus = QuestStatus.LOCKED
    rewards: Dict[str, int] = field(default_factory=dict)
    requirements: Dict[str, Any] = field(default_factory=dict)
    completion_condition: str = ""  # Что нужно сделать для завершения

@dataclass
class User:
    """Пользователь игры"""
    user_id: int
    username: Optional[str] = None
    language: Language = Language.RU
    resources: Resources = field(default_factory=Resources)
    level: int = 1
    experience: int = 0
    
    # Статус туториала и заданий
    tutorial_step: TutorialStep = TutorialStep.NOT_STARTED
    tutorial_completed: bool = False
    current_quests: List[Quest] = field(default_factory=list)
    
    # Персонаж
    character_preset: CharacterPreset = CharacterPreset.PRESET_1
    equipped_items: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "head": None,
        "body": "туника", 
        "feet": None  # босиком
    })
    
    # Лицензии и доступы
    has_island_access: bool = False      # Может ли войти на остров
    has_employer_license: bool = False
    has_farm_license: bool = False
    
    # Quantum Pass
    quantum_pass_until: Optional[datetime] = None
    
    # Мета
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    
    def has_quantum_pass(self) -> bool:
        """Проверка активности Quantum Pass"""
        return (self.quantum_pass_until is not None and 
                self.quantum_pass_until > datetime.now())
    
    def can_access_island(self) -> bool:
        """Может ли игрок войти на остров"""
        return self.has_island_access or self.tutorial_step in [
            TutorialStep.ISLAND_ACCESS_GRANTED,
            TutorialStep.TASK_HIRE_WORKER,
            TutorialStep.TASK_FIRST_WORK,
            TutorialStep.TASK_CITIZEN_QUEST,
            TutorialStep.TASK_TRAIN_SPECIALIST,
            TutorialStep.TASK_BUY_FARM_LICENSE,
            TutorialStep.TASK_BUY_LAND,
            TutorialStep.TASK_BUILD_CROP_BED,
            TutorialStep.TASK_PLANT_GRAIN,
            TutorialStep.TASK_BUILD_HENHOUSE,
            TutorialStep.TASK_BUY_CHICKEN,
            TutorialStep.COMPLETED
        ]
    
    def get_current_quest(self) -> Optional[Quest]:
        """Получить текущее активное задание"""
        for quest in self.current_quests:
            if quest.status == QuestStatus.AVAILABLE:
                return quest
        return None

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
    requirements: Dict[str, Any] = field(default_factory=dict)
    location: str = "sea"
    can_skip: bool = False  # Можно ли пропустить

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
    animal_type: str = "chicken"
    
    # Характеристики
    egg_production: int = 1
    health: int = 85
    fertility: int = 0
    lifespan: int = 30
    
    # Статус
    status: str = "alive"
    born_at: datetime = field(default_factory=datetime.now)
    last_fed: Optional[datetime] = None
    last_collected: Optional[datetime] = None

@dataclass
class LandPlot:
    """Участок земли"""
    plot_id: int
    owner_id: Optional[int] = None
    zone_type: str = "plains"
    zone_bonus: Dict[str, int] = field(default_factory=dict)
    price_rbtc: int = 0
    price_ryabucks: int = 1000
    status: str = "available"

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