# config/settings.py
"""
Настройки приложения с переключением между Supabase и PostgreSQL
"""

import os
from enum import Enum
from typing import Optional, List
from decimal import Decimal
import logging

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

class DatabaseType(Enum):
    """Тип базы данных"""
    SUPABASE = "supabase"
    POSTGRES = "postgres"

class CacheType(Enum):
    """Тип кэша"""
    MEMORY = "memory"
    REDIS = "redis"

class Settings:
    """Настройки приложения"""
    
    # ========== ОСНОВНЫЕ ==========
    APP_NAME: str = "Ryabot Island"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # ========== ПЕРЕКЛЮЧАТЕЛИ АРХИТЕКТУРЫ ==========
    DATABASE_TYPE: DatabaseType = DatabaseType(os.getenv("DATABASE_TYPE", "supabase"))
    CACHE_TYPE: CacheType = CacheType(os.getenv("CACHE_TYPE", "memory"))
    
    # ========== TELEGRAM BOT ==========
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "ryabotislandbot")
    
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не установлен в .env файле!")
    
    # ========== SUPABASE ==========
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")
    
    # ========== POSTGRESQL ==========
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ryabot_island")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    
    # ========== REDIS ==========
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # ========== АДМИНИСТРАТОРЫ ==========
    ADMIN_USER_IDS: List[int] = []
    
    admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
    if admin_ids_str:
        try:
            ADMIN_USER_IDS = [int(uid.strip()) for uid in admin_ids_str.split(",") if uid.strip()]
        except ValueError:
            print("⚠️ ВНИМАНИЕ: Неверный формат ADMIN_USER_IDS в .env")
    
    # ========== ФИЧИ ==========
    QUANTUM_PASS_ENABLED: bool = os.getenv("QUANTUM_PASS_ENABLED", "true").lower() == "true"
    BLOCKCHAIN_AUDIT_ENABLED: bool = os.getenv("BLOCKCHAIN_AUDIT_ENABLED", "true").lower() == "true"
    CHARACTERS_ENABLED: bool = os.getenv("CHARACTERS_ENABLED", "true").lower() == "true"
    
    # ========== ИГРОВЫЕ КОНСТАНТЫ ==========
    
    # Начальные ресурсы новых пользователей
    INITIAL_RYABUCKS: int = 100
    INITIAL_ENERGY: int = 30
    INITIAL_ENERGY_MAX: int = 30
    
    # Энергия
    ENERGY_REGEN_MINUTES: int = 48  # минут на восстановление 1 энергии
    ENERGY_FROM_AD: int = 30
    DAILY_AD_LIMIT: int = 3
    
    # RBTC
    RBTC_TOTAL_SUPPLY: int = 21_000_000
    BANK_INITIAL_RBTC: int = 1_050_000
    
    # Quantum Pass мультипликаторы
    QUANTUM_PASS_MULTIPLIERS = {
        "income": 2.0,      # x2 доход
        "speed": 2.0,       # x2 скорость
        "experience": 2.0,  # x2 опыт
        "rbtc": 2.0,       # x2 RBTC
        "golden_egg": 10.0, # x10 шанс золотого яйца
    }
    
    # Специалисты
    MAX_WORKERS_PER_HOUSE: int = 3
    MAX_HOUSES: int = 100
    
    # Ферма
    MAX_CHICKENS_PER_HENHOUSE: int = 25
    MAX_HENHOUSES: int = 100
    
    # Земля
    TOTAL_LAND_PLOTS: int = 10_000
    FIRST_PLOT_PRICE_RBTC: int = 200
    
    def validate_config(self) -> List[str]:
        """Проверка конфигурации"""
        errors = []
        
        if not self.BOT_TOKEN:
            errors.append("BOT_TOKEN не установлен")
        
        if self.DATABASE_TYPE == DatabaseType.SUPABASE:
            if not self.SUPABASE_URL or not self.SUPABASE_ANON_KEY:
                errors.append("SUPABASE_URL и SUPABASE_ANON_KEY должны быть установлены")
        
        if self.DATABASE_TYPE == DatabaseType.POSTGRES:
            if not self.POSTGRES_HOST or not self.POSTGRES_USER:
                errors.append("POSTGRES_HOST и POSTGRES_USER должны быть установлены")
        
        return errors

# Глобальный экземпляр настроек
settings = Settings()

# Проверяем конфигурацию
config_errors = settings.validate_config()
if config_errors:
    print("❌ ОШИБКИ КОНФИГУРАЦИИ:")
    for error in config_errors:
        print(f"   - {error}")
    print("\n💡 Проверьте файл .env")
    exit(1)

print(f"✅ Настройки загружены: {settings.DATABASE_TYPE.value} БД")


ADMIN_IDS = [
    6471957469
]
