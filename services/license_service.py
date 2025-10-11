# services/license_service.py (ФИНАЛЬНАЯ ПРАВИЛЬНАЯ ВЕРСИЯ)
"""
License Service - идеальная версия без синтаксических ошибок
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, List
from decimal import Decimal

from core.domain.entities import User
from core.ports.repositories import UserRepository
from services.event_tracker import get_event_tracker, EventType, EventSignificance
from adapters.database.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)

class LicenseType:
    """Типы лицензий в игре"""
    EMPLOYER = "employer"
    FARMER = "farmer"
    PARTNER = "partner"
    MERCHANT = "merchant"
    BANKER = "banker"
    POLITICAL = "political"
    RACING = "racing"
    FIGHTING = "fighting"
    QUANTUM = "quantum"
    EXPEDITION = "expedition"

LICENSE_CONFIG = {
    LicenseType.EMPLOYER: {
        "name": "Лицензия Работодателя",
        "icon": "💼",
        "base_price_ryabucks": 150,
        "base_price_rbtc": Decimal("1.5"),
        "max_level": 10,
        "description": "Количество рабочих",
        "telegra_link": "https://telegra.ph/Licenziya-Rabotodatelya-10-10",
    },
    LicenseType.FARMER: {
        "name": "Фермерская Лицензия",
        "icon": "🏡",
        "base_price_ryabucks": 200,
        "base_price_rbtc": Decimal("2.0"),
        "max_level": 8,
        "description": "Площадь фермы",
        "telegra_link": "https://telegra.ph/Fermerskaya-Licenziya-10-10",
    },
    LicenseType.PARTNER: {
        "name": "Партнёрская Лицензия",
        "icon": "👥",
        "base_price_ryabucks": 400,
        "base_price_rbtc": Decimal("4.0"),
        "max_level": 5,
        "description": "Рефералы",
        "telegra_link": "https://telegra.ph/Partnyerskaya-Licenziya-10-10",
    },
    LicenseType.MERCHANT: {
        "name": "Лицензия Продавца",
        "icon": "🍱",
        "base_price_ryabucks": 300,
        "base_price_rbtc": Decimal("3.0"),
        "max_level": 6,
        "description": "Торговля",
        "telegra_link": "https://telegra.ph/Licenziya-Prodavca-10-10",
    },
    LicenseType.BANKER: {
        "name": "Банковская Лицензия",
        "icon": "🏦",
        "base_price_ryabucks": 1000,
        "base_price_rbtc": Decimal("10.0"),
        "max_level": 4,
        "description": "Депозиты",
        "telegra_link": "https://telegra.ph/Bankovskaya-Licenziya-10-10",
    },
    LicenseType.POLITICAL: {
        "name": "Политическая Лицензия",
        "icon": "🏛️",
        "base_price_ryabucks": 1000,
        "base_price_rbtc": Decimal("10.0"),
        "max_level": 3,
        "description": "Управление",
        "telegra_link": "https://telegra.ph/Politicheskaya-Licenziya-10-10",
    },
    LicenseType.RACING: {
        "name": "Гоночная Лицензия",
        "icon": "🏇",
        "base_price_ryabucks": 800,
        "base_price_rbtc": Decimal("8.0"),
        "max_level": 5,
        "description": "Скачки",
        "telegra_link": "https://telegra.ph/Gonochnaya-Licenziya-10-10",
    },
    LicenseType.FIGHTING: {
        "name": "Бойцовская Лицензия",
        "icon": "🥊",
        "base_price_ryabucks": 600,
        "base_price_rbtc": Decimal("6.0"),
        "max_level": 5,
        "description": "Бои",
        "telegra_link": "https://telegra.ph/Bojcovskaya-Licenziya-10-10",
    },
    LicenseType.QUANTUM: {
        "name": "Квантовая Лицензия",
        "icon": "⚛️",
        "base_price_ryabucks": 1500,
        "base_price_rbtc": Decimal("15.0"),
        "max_level": 3,
        "description": "Исследования",
        "telegra_link": "https://telegra.ph/Kvantovaya-Licenziya-10-10",
    },
    LicenseType.EXPEDITION: {
        "name": "Экспедиционная Лицензия",
        "icon": "🏕️",
        "base_price_ryabucks": 500,
        "base_price_rbtc": Decimal("5.0"),
        "max_level": 5,
        "description": "Экспедиции",
        "telegra_link": "https://telegra.ph/Ekspedicionnaya-Licenziya-10-10",
    }
}

class LicenseService:
    """Система лицензий - правильная версия"""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.event_tracker = None
        self.client = None
        self.INITIAL_BANK_RYABUCKS = Decimal("1050000000")
        self.TOTAL_RBTC_POOL = Decimal("18480000")
        self.SMOOTHING_COEFFICIENT = 0.7

    async def _ensure_dependencies(self):
        """Подключаем зависимости"""
        if not self.event_tracker:
            self.event_tracker = await get_event_tracker()
        if not self.client:
            self.client = await get_supabase_client()

    async def calculate_price_multipliers(self) -> Dict[str, float]:
        """Рассчитать мультипликаторы цен"""
        try:
            await self._ensure_dependencies()

            pools = await self.client.execute_query(
                table="global_pools",
                operation="select"
            )

            total_bank_ryabucks = None

            for pool in pools:
                pool_name = pool.get("pool_name", "")
                if pool_name == "total_bank_ryabucks":
                    total_bank_ryabucks = Decimal(str(pool.get("ryabucks_amount", self.INITIAL_BANK_RYABUCKS)))

            if total_bank_ryabucks is None:
                total_bank_ryabucks = self.INITIAL_BANK_RYABUCKS

            ryabucks_multiplier = max(0.2, min(5.0, float(total_bank_ryabucks / self.INITIAL_BANK_RYABUCKS)))
            burned_rbtc = await self._get_total_burned_rbtc()
            burn_ratio = min(1.0, float(burned_rbtc / self.TOTAL_RBTC_POOL))
            rbtc_multiplier = max(0.1, 1.0 - (burn_ratio ** self.SMOOTHING_COEFFICIENT))

            return {
                "ryabucks": round(ryabucks_multiplier, 2),
                "rbtc": round(rbtc_multiplier, 2),
                "bank_ryabucks": float(total_bank_ryabucks),
                "burned_rbtc": float(burned_rbtc)
            }

        except Exception as e:
            logger.error(f"Ошибка расчёта мультипликаторов: {e}", exc_info=True)
            return {
                "ryabucks": 1.0,
                "rbtc": 1.0,
                "bank_ryabucks": float(self.INITIAL_BANK_RYABUCKS),
                "burned_rbtc": 0.0
            }

    async def _get_total_burned_rbtc(self) -> Decimal:
        """Получить сожженные RBTC"""
        try:
            stats = await self.client.execute_query(
                table="pool_statistics",
                operation="select",
                single=True
            )

            if stats and "total_rbtc_burned" in stats:
                return Decimal(str(stats.get("total_rbtc_burned", 0)))

            return Decimal("0")
        except:
            return Decimal("0")

    def calculate_license_price(self, license_type: str, level: int, multipliers: Dict[str, float]) -> Tuple[int, Decimal]:
        """Рассчитать стоимость лицензии"""
        if license_type not in LICENSE_CONFIG:
            return 0, Decimal("0")

        config = LICENSE_CONFIG[license_type]
        base_ryabucks = config["base_price_ryabucks"] * (2 ** (level - 1))
        base_rbtc = config["base_price_rbtc"] * (2 ** (level - 1))

        final_ryabucks = int(base_ryabucks * multipliers["ryabucks"])
        final_rbtc = base_rbtc * Decimal(str(multipliers["rbtc"]))

        return final_ryabucks, final_rbtc

    async def get_user_licenses(self, user_id: int) -> Dict[str, int]:
        """Получить лицензии пользователя"""
        try:
            await self._ensure_dependencies()

            licenses_data = await self.client.execute_query(
                table="user_licenses",
                operation="select",
                filters={"user_id": user_id}
            )

            licenses = {}
            if licenses_data:
                for license_data in licenses_data:
                    licenses[license_data["license_type"]] = license_data["level"]

            return licenses

        except Exception as e:
            logger.error(f"Ошибка получения лицензий для {user_id}: {e}", exc_info=True)
            return {}

    async def get_license_level(self, user_id: int, license_type: str) -> int:
        """Получить уровень лицензии"""
        licenses = await self.get_user_licenses(user_id)
        return licenses.get(license_type, 0)

    async def upgrade_license(self, user_id: int, license_type: str, currency: str) -> Tuple[bool, str]:
        """Улучшить лицензию пользователя"""
        try:
            await self._ensure_dependencies()

            if license_type not in LICENSE_CONFIG:
                return False, "Неизвестный тип лицензии"

            config = LICENSE_CONFIG[license_type]
            current_level = await self.get_license_level(user_id, license_type)
            next_level = current_level + 1

            if next_level > config["max_level"]:
                return False, f"Максимальный уровень достигнут ({config['max_level']})"

            # Рассчитываем цены
            multipliers = await self.calculate_price_multipliers()
            ryabucks_price, rbtc_price = self.calculate_license_price(license_type, next_level, multipliers)

            # Проверяем баланс пользователя
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return False, "Пользователь не найден"

            # Проверяем валюту и баланс
            if currency == "ryabucks":
                if user.resources.ryabucks < ryabucks_price:
                    return False, f"Недостаточно рябаксов. Нужно: {ryabucks_price:,}, есть: {user.resources.ryabucks:,}"
                price_to_pay = ryabucks_price
            elif currency == "rbtc":
                if user.resources.rbtc.amount < rbtc_price:
                    return False, f"Недостаточно RBTC. Нужно: {float(rbtc_price):.2f}, есть: {float(user.resources.rbtc.amount):.2f}"
                price_to_pay = rbtc_price
            else:
                return False, "Неизвестная валюта"

            # Списываем валюту
            if currency == "ryabucks":
                new_ryabucks = user.resources.ryabucks - ryabucks_price
                await self.user_repository.update_resources(
                    user_id=user_id,
                    updates={"ryabucks": new_ryabucks}
                )
            elif currency == "rbtc":
                new_rbtc = user.resources.rbtc.amount - rbtc_price
                await self.user_repository.update_resources(
                    user_id=user_id,
                    updates={"rbtc": float(new_rbtc)}
                )

                # Записываем сжигание RBTC
                await self._record_rbtc_burn(user_id, rbtc_price, f"license_{license_type}")

            # Проверяем существует ли лицензия
            existing_license = await self.client.execute_query(
                table="user_licenses",
                operation="select",
                filters={"user_id": user_id, "license_type": license_type},
                single=True
            )

            if existing_license:
                # Обновляем существующую лицензию
                await self.client.execute_query(
                    table="user_licenses",
                    operation="update",
                    data={"level": next_level},
                    filters={"user_id": user_id, "license_type": license_type}
                )
            else:
                # Создаём новую лицензию
                await self.client.execute_query(
                    table="user_licenses",
                    operation="insert",
                    data={
                        "user_id": user_id,
                        "license_type": license_type,
                        "level": next_level
                    }
                )

            # Трекаем событие
            if self.event_tracker:
                await self.event_tracker.track_currency_spent(
                    user_id=user_id,
                    currency_type=currency,
                    amount=float(price_to_pay) if currency == "rbtc" else price_to_pay,
                    reason=f"license_{license_type}"
                )

            logger.info(f"📜 Лицензия улучшена для {user_id}: {license_type} до уровня {next_level}")

            return True, f"✅ {config['name']} улучшена до уровня {next_level}!"

        except Exception as e:
            logger.error(f"Ошибка улучшения лицензии {license_type} для {user_id}: {e}", exc_info=True)
            return False, f"Техническая ошибка: {str(e)}"

    async def _record_rbtc_burn(self, user_id: int, amount: Decimal, reason: str):
        """Записать сжигание RBTC"""
        try:
            stats = await self.client.execute_query(
                table="pool_statistics",
                operation="select",
                single=True
            )

            if stats:
                current_burned = Decimal(str(stats.get("total_rbtc_burned", 0)))
                new_burned = current_burned + amount

                await self.client.execute_query(
                    table="pool_statistics",
                    operation="update",
                    data={"total_rbtc_burned": float(new_burned)},
                    filters={"id": stats["id"]}
                )
            else:
                await self.client.execute_query(
                    table="pool_statistics",
                    operation="insert",
                    data={"total_rbtc_burned": float(amount)}
                )

            logger.info(f"🔥 Сожжено {amount} RBTC ({reason})")

        except Exception as e:
            logger.warning(f"Не удалось записать сжигание RBTC: {e}")

    async def get_licenses_for_display(self, user_id: int) -> List[Dict]:
        """Получить лицензии для отображения"""
        try:
            multipliers = await self.calculate_price_multipliers()
            current_licenses = await self.get_user_licenses(user_id)

            result = []

            for license_type, config in LICENSE_CONFIG.items():
                current_level = current_licenses.get(license_type, 0)

                if current_level >= config["max_level"]:
                    result.append({
                        "type": license_type,
                        "icon": config["icon"],
                        "name": config["name"],
                        "current_level": current_level,
                        "max_level": config["max_level"],
                        "ryabucks_price": "MAX",
                        "rbtc_price": "MAX",
                        "telegra_link": config["telegra_link"],
                        "is_max": True
                    })
                else:
                    next_level = current_level + 1
                    ryabucks_price, rbtc_price = self.calculate_license_price(license_type, next_level, multipliers)

                    result.append({
                        "type": license_type,
                        "icon": config["icon"],
                        "name": config["name"],
                        "current_level": current_level,
                        "max_level": config["max_level"],
                        "ryabucks_price": f"{ryabucks_price:,}",
                        "rbtc_price": f"{float(rbtc_price):.2f}",
                        "ryabucks_price_raw": ryabucks_price,
                        "rbtc_price_raw": float(rbtc_price),
                        "telegra_link": config["telegra_link"],
                        "is_max": False
                    })

            return result

        except Exception as e:
            logger.error(f"Ошибка получения лицензий: {e}", exc_info=True)
            return []

    async def check_license_requirement(self, user_id: int, action: str, required_level: int = 1) -> bool:
        """Проверить требования лицензии"""
        action_requirements = {
            "hire_specialist": (LicenseType.EMPLOYER, 1),
            "buy_animal": (LicenseType.FARMER, 1),
            "build_structure": (LicenseType.FARMER, 1),
            "create_partnership": (LicenseType.PARTNER, 1),
            "trade_items": (LicenseType.MERCHANT, 1),
            "bank_operations": (LicenseType.BANKER, 1),
            "vote_proposal": (LicenseType.POLITICAL, 1),
            "horse_racing": (LicenseType.RACING, 1),
            "cockfight": (LicenseType.FIGHTING, 1),
            "quantum_research": (LicenseType.QUANTUM, 1),
            "start_expedition": (LicenseType.EXPEDITION, 1)
        }

        if action not in action_requirements:
            return True

        required_license, min_level = action_requirements[action]
        current_level = await self.get_license_level(user_id, required_license)

        return current_level >= max(min_level, required_level)


logger.info("✅ LicenseService загружен (ИДЕАЛЬНАЯ ВЕРСИЯ)")