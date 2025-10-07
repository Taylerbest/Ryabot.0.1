"""
Глобальные пулы экономики Ryabot Island
Общая эмиссия: 21 000 000 RBTC
"""
from decimal import Decimal

# ═════════════ ЭМИССИЯ ═════════════
TOTAL_RBTC_EMISSION = Decimal('21000000.0000')

# ════════ ГЛОБАЛЬНЫЕ ПУЛЫ (по GDD) ════════
GLOBAL_POOLS = {
    # Майнинг – Квантовые лаборатории (25 %)
    'mining': {
        'rbtc': Decimal('5250000.0000'),
        'percent': 25,
        'type': 'rewards',
        'description': 'Квантовые лаборатории'
    },

    # Рефералы – 3-уровневая система (20 %)
    'referrals': {
        'rbtc': Decimal('4200000.0000'),
        'percent': 20,
        'type': 'rewards',
        'description': '3-уровневая система'
    },

    # Экспедиции – Награды за риск (13 %)
    'expeditions': {
        'rbtc': Decimal('2730000.0000'),
        'percent': 13,
        'type': 'rewards',
        'description': 'Награды за риск'
    },

    # Петушиные бои – Турниры (10 %)
    'cockfights': {
        'rbtc': Decimal('2100000.0000'),
        'percent': 10,
        'type': 'tournament',
        'description': 'Турниры'
    },

    # Скачки – Турниры (7 %)
    'races': {
        'rbtc': Decimal('1470000.0000'),
        'percent': 7,
        'type': 'tournament',
        'description': 'Турниры'
    },

    # DEX листинг – Ликвидность (10 %)
    'dex_listing': {
        'rbtc': Decimal('2100000.0000'),
        'percent': 10,
        'type': 'liquidity',
        'description': 'Ликвидность'
    },

    # Лутбоксы – Элемент везения (6 %)
    'lootboxes': {
        'rbtc': Decimal('1260000.0000'),
        'percent': 6,
        'type': 'rewards',
        'description': 'Элемент везения'
    },

    # Игровой банк – Регулятор экономики (5 %)
    'game_bank': {
        'rbtc': Decimal('1050000.0000'),
        'percent': 5,
        'type': 'bank',
        'description': 'Регулятор экономики'
    },

    # Аномалии – Пассивная добыча (4 %)
    'anomalies': {
        'rbtc': Decimal('840000.0000'),
        'percent': 4,
        'type': 'rewards',
        'description': 'Пассивная добыча'
    }
}

# ════════ ПУЛЫ ИГРОВОГО БАНКА ════════
BANK_POOLS = {
    'rbtc_pool': Decimal('1050000.0000'),       # 5 % от эмиссии
    'ryabucks_pool': Decimal('105000000.0000'), # начальный курс 1:100
    'total_invested_golden_eggs': 0
}

# ════════ ПАРАМЕТРЫ ОБМЕНА ════════
INITIAL_EXCHANGE_RATE = 100               # стартовый курс
STARS_PACKAGE_BASE   = 100                # базовый пакет ⭐
RBTC_EQUIVALENT      = Decimal('14.3')    # RBTC за 100 ⭐

# ════════ ФУНКЦИИ ДИНАМИКИ КУРСА ════════
def calculate_current_rate(rbtc_pool: Decimal,
                           ryabucks_pool: Decimal) -> Decimal:
    """Текущий курс: ryabucks / rbtc."""
    return Decimal('0') if rbtc_pool == 0 else ryabucks_pool / rbtc_pool


def calculate_stars_to_ryabucks(stars: int,
                                current_rate: Decimal) -> int:
    """
    Сколько рябаксов даёт донат в Stars:
    (stars/100) × 14.3 RBTC × текущий курс.
    """
    rbtc_amount    = Decimal(stars) / STARS_PACKAGE_BASE * RBTC_EQUIVALENT
    ryabucks       = rbtc_amount * current_rate
    return int(ryabucks)  # округляем до целого


def _constant_product_k(rbtc_pool: Decimal,
                        ryabucks_pool: Decimal) -> Decimal:
    return rbtc_pool * ryabucks_pool


def calculate_buy_rbtc_cost(amount: Decimal,
                             rbtc_pool: Decimal,
                             ryabucks_pool: Decimal) -> int:
    """Стоимость покупки RBTC по формуле x·y=k."""
    if amount >= rbtc_pool:
        raise ValueError('Недостаточно RBTC в пуле')
    k                = _constant_product_k(rbtc_pool, ryabucks_pool)
    new_rbtc_pool    = rbtc_pool - amount
    new_ryabucks_pool= k / new_rbtc_pool
    return int(new_ryabucks_pool - ryabucks_pool)


def calculate_sell_rbtc_reward(amount: Decimal,
                               rbtc_pool: Decimal,
                               ryabucks_pool: Decimal) -> int:
    """Награда в рябаксах за продажу RBTC."""
    k                = _constant_product_k(rbtc_pool, ryabucks_pool)
    new_rbtc_pool    = rbtc_pool + amount
    new_ryabucks_pool= k / new_rbtc_pool
    return int(ryabucks_pool - new_ryabucks_pool)

# ════════ ЛИМИТЫ ОПЕРАЦИЙ ════════
TRANSACTION_LIMITS = {
    'min_rbtc_trade'       : Decimal('0.0001'),
    'max_rbtc_trade'       : Decimal('10000'),
    'min_ryabucks_trade'   : 10,
    'daily_withdrawal_limit': Decimal('1000'),
    'min_stars_purchase'   : 100,
    'max_stars_purchase'   : 10000
}

# ════════ ПАКЕТЫ STARS ════════
STARS_PACKAGES = [
    {'stars': 100,  'bonus': 0},
    {'stars': 250,  'bonus': 5},
    {'stars': 500,  'bonus': 10},
    {'stars': 1000, 'bonus': 15},
    {'stars': 2500, 'bonus': 20},
    {'stars': 5000, 'bonus': 25},
]

# ════════ ОТОБРАЖЕНИЕ ════════
POOL_DISPLAY_NAMES = {
    'mining'      : 'Майнинг',
    'referrals'   : 'Рефералы',
    'expeditions' : 'Экспедиции',
    'cockfights'  : 'Петушиные бои',
    'races'       : 'Скачки',
    'dex_listing' : 'DEX листинг',
    'lootboxes'   : 'Лутбоксы',
    'game_bank'   : 'Игровой банк',
    'anomalies'   : 'Аномалии'
}
