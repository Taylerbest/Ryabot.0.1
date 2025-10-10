# services/specialist_service.py
"""
Specialist Service - система найма и управления специалистами (версия GDD)
Интегрирована с энергией, лицензиями и EventTracker
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from enum import Enum

from core.domain.entities import User, Specialist
from core.ports.repositories import UserRepository
from services.event_tracker import get_event_tracker, EventType, EventSignificance
from services.license_service import LicenseService, LicenseType
from services.energy_service import EnergyService
from adapters.database.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)

class SpecialistType(Enum):
    """Типы специалистов по GDD"""
    LABORER = "laborer"           # Рабочий 🙍‍♂️
    FARMER = "farmer"             # Фермер 👩‍🌾
    BUILDER = "builder"           # Строитель 👷
    COOK = "cook"                 # Повар 🧑‍🍳
    FISHERMAN = "fisherman"       # Рыбак 🎣
    FORESTER = "forester"         # Лесник 👨‍🚒
    SCIENTIST = "scientist"       # Учёный 🧑‍🔬
    Q_SOLDIER = "q_soldier"       # Q-Солдат 💂
    DOCTOR = "doctor"             # Доктор 🧑‍⚕️
    TEACHER = "teacher"           # Учитель 🧑‍🏫

# Конфигурация специалистов по GDD
SPECIALIST_CONFIG = {
    SpecialistType.LABORER: {
        "name": "Рабочий",
        "icon": "🙍‍♂️",
        "base_price_ryabucks": 50,
        "base_price_experience": 10,
        "energy_cost": 5,
        "license_required": LicenseType.EMPLOYER,
        "license_level": 1,
        "description": "Универсальный работник для различных задач",
        "work_locations": ["city", "farm", "construction"],
        "base_income": {"min": 10, "max": 20},
        "training_time_hours": 5,
        "expedition_suitable": False,
        "max_hp": 30,
        "base_stats": {
            "attack": 25,
            "defense": 30, 
            "hp": 30,
            "cost_rbtc": 0.2,
            "efficiency": 80,
            "income_min": 10,
            "income_max": 20,
            "healing_cost": 40,
            "healing_time": 4
        }
    },
    SpecialistType.FARMER: {
        "name": "Фермер", 
        "icon": "👩‍🌾",
        "base_price_ryabucks": 75,
        "base_price_experience": 15,
        "energy_cost": 3,
        "license_required": LicenseType.FARMER,
        "license_level": 1,
        "description": "Специалист по животноводству и растениеводству",
        "work_locations": ["farm", "garden", "stable"],
        "base_income": {"min": 15, "max": 30},
        "training_time_hours": 10,
        "expedition_suitable": False,
        "max_hp": 42,
        "base_stats": {
            "attack": 20,
            "defense": 30,
            "hp": 42,
            "cost_rbtc": 0.35,
            "efficiency": 180,
            "income_min": 8,
            "income_max": 16,
            "healing_cost": 40,
            "healing_time": 4
        }
    },
    SpecialistType.BUILDER: {
        "name": "Строитель",
        "icon": "👷", 
        "base_price_ryabucks": 100,
        "base_price_experience": 20,
        "energy_cost": 5,
        "license_required": LicenseType.FARMER, # Используем фермерскую для строительства
        "license_level": 2,
        "description": "Специалист по возведению и ремонту зданий",
        "work_locations": ["construction", "city", "buildings"],
        "base_income": {"min": 20, "max": 35},
        "training_time_hours": 15,
        "expedition_suitable": False,
        "max_hp": 53,
        "base_stats": {
            "attack": 35,
            "defense": 40,
            "hp": 53,
            "cost_rbtc": 0.5,
            "efficiency": 150,
            "income_min": 15,
            "income_max": 25,
            "healing_cost": 60,
            "healing_time": 6
        }
    },
    SpecialistType.COOK: {
        "name": "Повар",
        "icon": "🧑‍🍳",
        "base_price_ryabucks": 60,
        "base_price_experience": 12,
        "energy_cost": 3,
        "license_required": LicenseType.MERCHANT,
        "license_level": 1,
        "description": "Мастер кулинарии и пищевой промышленности",
        "work_locations": ["kitchen", "restaurant", "farm"],
        "base_income": {"min": 10, "max": 30},
        "training_time_hours": 5,
        "expedition_suitable": False,
        "max_hp": 46,
        "base_stats": {
            "attack": 20,
            "defense": 25,
            "hp": 46,
            "cost_rbtc": 0.3,
            "efficiency": 300,
            "income_min": 5,
            "income_max": 10,
            "healing_cost": 30,
            "healing_time": 3
        }
    },
    SpecialistType.FISHERMAN: {
        "name": "Рыбак",
        "icon": "🎣",
        "base_price_ryabucks": 85,
        "base_price_experience": 18,
        "energy_cost": 4,
        "license_required": LicenseType.EMPLOYER,
        "license_level": 2,
        "description": "Специалист по морским и речным промыслам",
        "work_locations": ["sea", "river", "fishing"],
        "base_income": {"min": 25, "max": 40},
        "training_time_hours": 25,
        "expedition_suitable": False,
        "max_hp": 45,
        "base_stats": {
            "attack": 30,
            "defense": 50,
            "hp": 45,
            "cost_rbtc": 0.8,
            "efficiency": 60,
            "income_min": 25,
            "income_max": 40,
            "healing_cost": 80,
            "healing_time": 8
        }
    },
    SpecialistType.FORESTER: {
        "name": "Лесник",
        "icon": "👨‍🚒",
        "base_price_ryabucks": 90,
        "base_price_experience": 20,
        "energy_cost": 4,
        "license_required": LicenseType.EMPLOYER,
        "license_level": 2,
        "description": "Специалист по лесозаготовке и охране природы",
        "work_locations": ["forest", "lumber", "nature"],
        "base_income": {"min": 20, "max": 35},
        "training_time_hours": 30,
        "expedition_suitable": True,
        "max_hp": 55,
        "base_stats": {
            "attack": 35,
            "defense": 50,
            "hp": 55,
            "cost_rbtc": 2.0,
            "efficiency": 100,
            "income_min": 20,
            "income_max": 35,
            "healing_cost": 60,
            "healing_time": 6
        }
    },
    SpecialistType.SCIENTIST: {
        "name": "Учёный",
        "icon": "🧑‍🔬",
        "base_price_ryabucks": 180,
        "base_price_experience": 50,
        "energy_cost": 6,
        "license_required": LicenseType.QUANTUM,
        "license_level": 1,
        "description": "Исследователь квантовых технологий",
        "work_locations": ["laboratory", "research", "quantum"],
        "base_income": {"min": 30, "max": 55},
        "training_time_hours": 30,
        "expedition_suitable": False,
        "max_hp": 42,
        "base_stats": {
            "attack": 30,
            "defense": 30,
            "hp": 42,
            "cost_rbtc": 3.0,
            "efficiency": 120,
            "income_min": 12,
            "income_max": 24,
            "healing_cost": 40,
            "healing_time": 4
        }
    },
    SpecialistType.Q_SOLDIER: {
        "name": "Q-Солдат",
        "icon": "💂",
        "base_price_ryabucks": 400,
        "base_price_experience": 100,
        "energy_cost": 15,
        "license_required": LicenseType.EXPEDITION,
        "license_level": 3,
        "description": "Элитный боец с квантовым оснащением",
        "work_locations": ["military", "expeditions", "combat"],
        "base_income": {"min": 50, "max": 80},
        "training_time_hours": 40,
        "expedition_suitable": True,
        "max_hp": 63,
        "base_stats": {
            "attack": 60,
            "defense": 55,
            "hp": 63,
            "cost_rbtc": 0.5,
            "efficiency": 50,
            "income_min": 35,
            "income_max": 50,
            "healing_cost": 80,
            "healing_time": 8
        }
    },
    SpecialistType.DOCTOR: {
        "name": "Доктор",
        "icon": "🧑‍⚕️",
        "base_price_ryabucks": 150,
        "base_price_experience": 40,
        "energy_cost": 5,
        "license_required": LicenseType.EMPLOYER,
        "license_level": 3,
        "description": "Медик для лечения раненых специалистов",
        "work_locations": ["hospital", "medical", "clinic"],
        "base_income": {"min": 15, "max": 30},
        "training_time_hours": 10,
        "expedition_suitable": False,
        "max_hp": 58,
        "base_stats": {
            "attack": 25,
            "defense": 35,
            "hp": 58,
            "cost_rbtc": 0.8,
            "efficiency": 200,
            "income_min": 8,
            "income_max": 15,
            "healing_cost": 50,
            "healing_time": 5
        }
    },
    SpecialistType.TEACHER: {
        "name": "Учитель",
        "icon": "🧑‍🏫",
        "base_price_ryabucks": 120,
        "base_price_experience": 30,
        "energy_cost": 4,
        "license_required": LicenseType.EMPLOYER,
        "license_level": 2,
        "description": "Наставник для обучения других специалистов",
        "work_locations": ["academy", "school", "training"],
        "base_income": {"min": 20, "max": 40},
        "training_time_hours": 12,
        "expedition_suitable": False,
        "max_hp": 40,
        "base_stats": {
            "attack": 30,
            "defense": 30,
            "hp": 40,
            "cost_rbtc": 1.2,
            "efficiency": 150,
            "income_min": 10,
            "income_max": 20,
            "healing_cost": 45,
            "healing_time": 4
        }
    }
}

class SpecialistService:
    """Сервис управления специалистами (версия GDD)"""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.license_service = None
        self.energy_service = None
        self.event_tracker = None
        self.client = None

    async def _ensure_dependencies(self):
        """Подключаем зависимости"""
        if not self.license_service:
            self.license_service = LicenseService(self.user_repository)
        if not self.energy_service:
            self.energy_service = EnergyService(self.user_repository)
        if not self.event_tracker:
            self.event_tracker = await get_event_tracker()
        if not self.client:
            self.client = await get_supabase_client()

    async def get_available_specialists(self, user_id: int) -> List[Dict]:
        """Получить доступных для найма специалистов"""
        try:
            await self._ensure_dependencies()

            # Получаем лицензии пользователя
            user_licenses = await self.license_service.get_user_licenses(user_id)

            # Получаем мультипликаторы цен
            multipliers = await self.license_service.calculate_price_multipliers()

            available = []

            for spec_type, config in SPECIALIST_CONFIG.items():
                # Проверяем лицензию
                license_type = config["license_required"]
                required_level = config["license_level"]
                current_level = user_licenses.get(license_type.value, 0)

                if current_level >= required_level:
                    # Рассчитываем цену с мультипликатором
                    base_price = config["base_price_ryabucks"]
                    final_price = int(base_price * multipliers["ryabucks"])

                    # Рассчитываем цену в RBTC если есть
                    rbtc_price = None
                    if "cost_rbtc" in config["base_stats"]:
                        base_rbtc = Decimal(str(config["base_stats"]["cost_rbtc"]))
                        final_rbtc = base_rbtc * Decimal(str(multipliers["rbtc"]))
                        rbtc_price = float(final_rbtc)

                    available.append({
                        "type": spec_type.value,
                        "name": config["name"],
                        "icon": config["icon"],
                        "price_ryabucks": final_price,
                        "price_rbtc": rbtc_price,
                        "price_experience": config["base_price_experience"],
                        "energy_cost": config["energy_cost"],
                        "description": config["description"],
                        "work_locations": config["work_locations"],
                        "base_income": config["base_income"],
                        "training_time_hours": config["training_time_hours"],
                        "expedition_suitable": config.get("expedition_suitable", False),
                        "max_hp": config["max_hp"],
                        "base_stats": config["base_stats"],
                        "can_afford": True  # Проверим при найме
                    })

            return available

        except Exception as e:
            logger.error(f"Ошибка получения доступных специалистов для {user_id}: {e}")
            return []

    async def hire_specialist(self, user_id: int, specialist_type: str, currency: str = "ryabucks") -> Tuple[bool, str]:
        """
        Нанять специалиста
        currency: 'ryabucks' или 'rbtc'
        Возвращает (успех, сообщение)
        """
        try:
            await self._ensure_dependencies()

            # Валидация типа специалиста
            try:
                spec_enum = SpecialistType(specialist_type)
            except ValueError:
                return False, "Неизвестный тип специалиста"

            config = SPECIALIST_CONFIG[spec_enum]

            # Проверяем лицензию
            license_type = config["license_required"]
            required_level = config["license_level"]
            current_level = await self.license_service.get_license_level(user_id, license_type)

            if current_level < required_level:
                from services.license_service import LICENSE_CONFIG
                license_name = LICENSE_CONFIG[license_type]["name"]
                return False, f"Требуется {license_name} уровня {required_level}. У вас уровень {current_level}"

            # Проверяем энергию
            energy_cost = config["energy_cost"]
            can_afford_energy, energy_msg = await self.energy_service.can_perform_action(user_id, energy_cost)

            if not can_afford_energy:
                return False, f"Недостаточно энергии. {energy_msg}"

            # Получаем пользователя и проверяем ресурсы
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return False, "Пользователь не найден"

            # Рассчитываем цены
            multipliers = await self.license_service.calculate_price_multipliers()
            ryabucks_cost = int(config["base_price_ryabucks"] * multipliers["ryabucks"])
            experience_cost = config["base_price_experience"]

            # Определяем валюту и стоимость
            if currency == "ryabucks":
                if user.resources.ryabucks < ryabucks_cost:
                    return False, f"Недостаточно рябаксов. Нужно: {ryabucks_cost:,}, есть: {user.resources.ryabucks:,}"
                cost_to_pay = ryabucks_cost
            elif currency == "rbtc":
                if "cost_rbtc" not in config["base_stats"]:
                    return False, "Этого специалиста нельзя купить за RBTC"

                base_rbtc = Decimal(str(config["base_stats"]["cost_rbtc"]))
                rbtc_cost = base_rbtc * Decimal(str(multipliers["rbtc"]))

                if user.resources.rbtc.amount < rbtc_cost:
                    return False, f"Недостаточно RBTC. Нужно: {rbtc_cost:.2f}, есть: {user.resources.rbtc.amount}"
                cost_to_pay = rbtc_cost
            else:
                return False, "Неизвестная валюта"

            # Проверяем жидкий опыт
            if user.resources.liquid_experience < experience_cost:
                return False, f"Недостаточно жидкого опыта. Нужно: {experience_cost}, есть: {user.resources.liquid_experience}"

            # Проверяем лимиты найма
            current_specialists = await self._get_user_specialists_count(user_id)
            max_specialists = await self._get_max_specialists(user_id)

            if current_specialists >= max_specialists:
                return False, f"Достигнут лимит специалистов: {max_specialists}. Улучшите лицензию работодателя."

            # Выполняем найм в транзакции
            async with self.client.transaction() as tx:
                # Списываем ресурсы
                updates = {"liquid_experience": user.resources.liquid_experience - experience_cost}

                if currency == "ryabucks":
                    updates["ryabucks"] = user.resources.ryabucks - ryabucks_cost
                elif currency == "rbtc":
                    updates["rbtc"] = user.resources.rbtc.amount - cost_to_pay
                    # Записываем сжигание RBTC
                    await self._record_rbtc_burn(user_id, cost_to_pay, f"hire_{specialist_type}")

                await self.user_repository.update_resources(user_id=user_id, updates=updates)

                # Списываем энергию
                energy_consumed = await self.energy_service.consume_energy(user_id, energy_cost)
                if not energy_consumed:
                    return False, "Не удалось списать энергию"

                # Создаём специалиста
                specialist_id = await self._create_specialist(user_id, spec_enum, config)

            # Трекаем события
            await self.event_tracker.track_currency_spent(
                user_id=user_id,
                currency_type=currency,
                amount=cost_to_pay,
                reason=f"hire_{specialist_type}"
            )

            await self.event_tracker.track_specialist_hiring(
                user_id=user_id,
                specialist_type=specialist_type,
                cost=int(cost_to_pay) if currency == "ryabucks" else float(cost_to_pay)
            )

            logger.info(f"👷 Специалист нанят для {user_id}: {config['name']} за {cost_to_pay} {currency}")

            return True, f"✅ {config['name']} {config['icon']} успешно нанят!\nПотрачено: {cost_to_pay:,} {currency}, {experience_cost} опыта, {energy_cost} энергии"

        except Exception as e:
            logger.error(f"Ошибка найма специалиста {specialist_type} для {user_id}: {e}")
            return False, "Техническая ошибка при найме"

    async def _create_specialist(self, user_id: int, spec_type: SpecialistType, config: Dict) -> int:
        """Создать специалиста в БД с характеристиками из GDD"""
        import random

        base_stats = config["base_stats"]

        # Генерируем характеристики на основе GDD
        efficiency = base_stats.get("efficiency", 100) + random.randint(-10, 10)  # ±10%
        loyalty = random.randint(85, 100)
        experience = 0
        max_hp = config["max_hp"]
        current_hp = max_hp

        # Боевые характеристики
        combat_stats = {
            "attack": base_stats.get("attack", 10),
            "defense": base_stats.get("defense", 10),
            "health": max_hp,
            "max_health": max_hp
        } if config.get("expedition_suitable") else {}

        # Сохраняем в БД
        specialist_data = {
            "user_id": user_id,
            "specialist_type": spec_type.value,
            "name": f"{config['name']} #{random.randint(1000, 9999)}",
            "efficiency": efficiency,
            "loyalty": loyalty,
            "experience": experience,
            "current_hp": current_hp,
            "max_hp": max_hp,
            "combat_stats": combat_stats if combat_stats else None,
            "hired_at": datetime.now(timezone.utc).isoformat(),
            "status": "available",  # available, working, training, injured, dead
            "last_work_at": None,
            "healing_cost": base_stats.get("healing_cost", 50),
            "healing_time_hours": base_stats.get("healing_time", 4)
        }

        result = await self.client.execute_query(
            table="user_specialists",
            operation="insert",
            data=specialist_data
        )

        return result[0]["id"] if result else None

    async def _record_rbtc_burn(self, user_id: int, amount: Decimal, reason: str):
        """Записать сжигание RBTC в audit_log"""
        await self.event_tracker.track_event(
            user_id=user_id,
            event_type=EventType.RBTC_TRANSACTION,
            data={
                "type": "burn",
                "amount": float(amount),
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            significance=EventSignificance.IMPORTANT
        )

    async def _get_user_specialists_count(self, user_id: int) -> int:
        """Получить количество специалистов пользователя"""
        try:
            specialists = await self.client.execute_query(
                table="user_specialists",
                operation="select",
                columns=["id"],
                filters={
                    "user_id": user_id, 
                    "status": ["available", "working", "training", "injured"]
                }
            )
            return len(specialists)
        except:
            return 0

    async def _get_max_specialists(self, user_id: int) -> int:
        """Получить максимальное количество специалистов по лицензии"""
        employer_level = await self.license_service.get_license_level(user_id, LicenseType.EMPLOYER)

        # Лимиты по уровням лицензии работодателя (из GDD)
        if employer_level >= 10:
            return 999  # Безлимит
        elif employer_level >= 5:
            return 25   # Q-Солдаты доступны
        elif employer_level >= 3:
            return 10
        elif employer_level >= 2:
            return 6
        elif employer_level >= 1:
            return 3
        else:
            return 0    # Нет лицензии

    async def get_user_specialists(self, user_id: int) -> List[Dict]:
        """Получить список специалистов пользователя"""
        try:
            await self._ensure_dependencies()

            specialists_data = await self.client.execute_query(
                table="user_specialists",
                operation="select",
                filters={"user_id": user_id}
            )

            specialists = []
            for data in specialists_data:
                config = SPECIALIST_CONFIG.get(SpecialistType(data["specialist_type"]), {})

                specialists.append({
                    "id": data["id"],
                    "type": data["specialist_type"],
                    "name": data["name"],
                    "icon": config.get("icon", "👤"),
                    "efficiency": data["efficiency"],
                    "loyalty": data["loyalty"],
                    "experience": data["experience"],
                    "current_hp": data["current_hp"],
                    "max_hp": data["max_hp"],
                    "status": data["status"],
                    "combat_stats": data.get("combat_stats", {}),
                    "hired_at": data["hired_at"],
                    "last_work_at": data.get("last_work_at"),
                    "healing_cost": data.get("healing_cost", 50),
                    "healing_time_hours": data.get("healing_time_hours", 4)
                })

            return specialists

        except Exception as e:
            logger.error(f"Ошибка получения специалистов для {user_id}: {e}")
            return []

    async def heal_specialist(self, user_id: int, specialist_id: int) -> Tuple[bool, str]:
        """Вылечить раненого специалиста"""
        try:
            await self._ensure_dependencies()

            # Получаем специалиста
            specialist_data = await self.client.execute_query(
                table="user_specialists",
                operation="select",
                filters={"id": specialist_id, "user_id": user_id}
            )

            if not specialist_data:
                return False, "Специалист не найден"

            specialist = specialist_data[0]

            if specialist["status"] != "injured":
                return False, "Специалист не ранен"

            if specialist["current_hp"] >= specialist["max_hp"]:
                return False, "Специалист уже здоров"

            # Проверяем баланс
            user = await self.user_repository.get_by_id(user_id)
            healing_cost = specialist.get("healing_cost", 50)

            if user.resources.ryabucks < healing_cost:
                return False, f"Недостаточно рябаксов для лечения. Нужно: {healing_cost}"

            # Лечим
            async with self.client.transaction() as tx:
                # Списываем рябаксы
                await self.user_repository.update_resources(
                    user_id=user_id,
                    updates={"ryabucks": user.resources.ryabucks - healing_cost}
                )

                # Восстанавливаем здоровье
                await self.client.execute_query(
                    table="user_specialists",
                    operation="update",
                    data={
                        "current_hp": specialist["max_hp"],
                        "status": "available"
                    },
                    filters={"id": specialist_id}
                )

            # Трекаем лечение
            await self.event_tracker.track_currency_spent(
                user_id=user_id,
                currency_type="ryabucks", 
                amount=healing_cost,
                reason=f"heal_specialist_{specialist_id}"
            )

            logger.info(f"🏥 Специалист вылечен для {user_id}: {specialist['name']} за {healing_cost} рябаксов")

            return True, f"✅ {specialist['name']} успешно вылечен за {healing_cost} рябаксов!"

        except Exception as e:
            logger.error(f"Ошибка лечения специалиста {specialist_id} для {user_id}: {e}")
            return False, "Техническая ошибка при лечении"

    # Заглушки для функций в разработке
    async def train_specialist(self, user_id: int, specialist_id: int) -> Tuple[bool, str]:
        """Отправить специалиста на обучение в академию"""
        return False, "🚧 Академия в разработке"

    async def assign_work(self, user_id: int, specialist_id: int, location: str) -> Tuple[bool, str]:
        """Отправить специалиста на работу"""
        return False, "🚧 Система работ в разработке"


logger.info("✅ SpecialistService (GDD версия) загружен")