# interfaces/telegram_bot/states.py
"""
FSM состояния для бота
"""

from aiogram.fsm.state import State, StatesGroup

class MenuState(StatesGroup):
    """Состояния меню"""
    LANGUAGE_SELECTION = State()    # Выбор языка при первом запуске
    OUTSIDE_ISLAND = State()        # Вне острова (стартовое меню)
    ON_ISLAND = State()            # На острове (основное меню)
    IN_TOWN = State()              # В городе
    IN_ACADEMY = State()           # В академии
    IN_TUTORIAL = State()          # Проходит туториал

class TutorialState(StatesGroup):
    """Состояния туториала"""
    SHIPWRECK = State()            # Кораблекрушение
    WAKE_UP = State()             # Пробуждение на берегу
    EXPLORE = State()             # Исследование острова
    FIND_RESOURCES = State()      # Поиск ресурсов
    HIRE_WORKER = State()         # Найм первого жителя
    TRAINING = State()            # Обучение жителя
    COMPLETE = State()            # Завершение туториала

class AcademyState(StatesGroup):
    """Состояния академии"""
    MAIN_MENU = State()           # Главное меню академии
    LABOR_EXCHANGE = State()      # Биржа труда (найм рабочих)
    EXPERT_COURSES = State()      # Курсы экспертов (обучение специалистов)
    TRAINING_CLASS = State()      # Класс обучения

# ═══ СОСТОЯНИЯ БАНКА (РЯБАНК) ═══
class BankState(StatesGroup):
    """Состояния для работы с банком"""
    MAIN_MENU = State()
    BUY_RBTC_AMOUNT = State()
    BUY_RBTC_CONFIRM = State()
    SELL_RBTC_AMOUNT = State()
    SELL_RBTC_CONFIRM = State()
    BUY_RYABUCKS_STARS = State()
    INVEST_GOLDEN_EGG = State()
    SEND_RBTC_USER = State()
    SEND_RBTC_AMOUNT = State()
    SEND_RBTC_CONFIRM = State()

# ═══ СОСТОЯНИЯ ПРОПУСКА (КВАНТХАБ) ═══
class QuantumPassState(StatesGroup):
    MAIN_MENU = State()
    PURCHASE_CONFIRM = State()
