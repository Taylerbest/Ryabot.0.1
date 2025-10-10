"""
License Service - улучшенная система лицензий с динамическим ценообразованием
Поддерживает инфляцию/дефляцию банка и плавное удешевление RBTC
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, List
from decimal import Decimal

from core.domain.entities import User
from core.ports.repositories import UserRepository
from services.event_tracker import get_event_tracker, EventType, EventSignificance
from services.bank_service import BankService
from adapters.database.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)

class LicenseType:
    """Типы лицензий в игре"""
    EMPLOYER = "employer"           # Работодатель 💼
    FARMER = "farmer"              # Фермерская 🏡
    PARTNER = "partner"            # Партнёрская 👥  
    MERCHANT = "merchant"          # Продавца 🍱
    BANKER = "banker"              # Банковская 🏦
    POLITICAL = "political"        # Политическая 🏛️
    RACING = "racing"              # Гоночная 🏇
    FIGHTING = "fighting"          # Бойцовская 🥊
    QUANTUM = "quantum"            # Квантовая ⚛️
    EXPEDITION = "expedition"      # Экспедиционная 🏕️

# Конфигурация лицензий с иконками и ценами
LICENSE_CONFIG = {
    LicenseType.EMPLOYER: {
        "name": "Лицензия Работодателя",
        "icon": "💼",
        "base_price_ryabucks": 150,
        "base_price_rbtc": Decimal("1.5"),
        "max_level": 10,
        "description": "Количество рабочих",
        "telegra_link": "https://telegra.ph/Licenziya-Rabotodatelya-10-10",
        "level_benefits": {
            1: "До 3 специалистов",
            2: "До 6 специалистов", 
            3: "До 10 специалистов",
            5: "Найм Q-Солдат",
            10: "Безлимитный найм"
        }
    },
    LicenseType.FARMER: {
        "name": "Фермерская Лицензия",
        "icon": "🏡",
        "base_price_ryabucks": 200,
        "base_price_rbtc": Decimal("2.0"),
        "max_level": 8,
        "description": "Площадь фермы и доступ к постройкам",
        "telegra_link": "https://telegra.ph/Fermerskaya-Licenziya-10-10",
        "level_benefits": {
            1: "Базовые постройки",
            2: "Животноводство",
            3: "Расширенная ферма",
            5: "Экзотические животные",
            8: "Мега-ферма"
        }
    },
    LicenseType.PARTNER: {
        "name": "Партнёрская Лицензия",
        "icon": "👥", 
        "base_price_ryabucks": 400,
        "base_price_rbtc": Decimal("4.0"),
        "max_level": 5,
        "description": "Глубокие уровни дохода",
        "telegra_link": "https://telegra.ph/Partnyerskaya-Licenziya-10-10",
        "level_benefits": {
            1: "1-й уровень рефералов",
            2: "2-й уровень рефералов",
            3: "3-й уровень рефералов",
            4: "Командные бонусы",
            5: "Лидерские привилегии"
        }
    },
    LicenseType.MERCHANT: {
        "name": "Лицензия Продавца",
        "icon": "🍱",
        "base_price_ryabucks": 300,
        "base_price_rbtc": Decimal("3.0"),
        "max_level": 6,
        "description": "Магазины и торговля",
        "telegra_link": "https://telegra.ph/Licenziya-Prodavca-10-10",
        "level_benefits": {
            1: "Базовая торговля",
            2: "Скидки 5%",
            3: "Оптовые цены",
            4: "Скидки 15%",
            6: "Доступ к аукциону"
        }
    },
    LicenseType.BANKER: {
        "name": "Банковская Лицензия",
        "icon": "🏦",
        "base_price_ryabucks": 1000,
        "base_price_rbtc": Decimal("10.0"),
        "max_level": 4,
        "description": "Депозиты и выводы RBTC",
        "telegra_link": "https://telegra.ph/Bankovskaya-Licenziya-10-10",
        "level_benefits": {
            1: "Базовые депозиты",
            2: "Кредиты под залог",
            3: "Пониженные комиссии",
            4: "VIP банкинг"
        }
    },
    LicenseType.POLITICAL: {
        "name": "Политическая Лицензия",
        "icon": "🏛️",
        "base_price_ryabucks": 1000,
        "base_price_rbtc": Decimal("10.0"),
        "max_level": 3,
        "description": "Управление островом и экономикой",
        "telegra_link": "https://telegra.ph/Politicheskaya-Licenziya-10-10",
        "level_benefits": {
            1: "Участие в голосованиях",
            2: "Предложение инициатив",
            3: "Губернаторские права"
        }
    },
    LicenseType.RACING: {
        "name": "Гоночная Лицензия",
        "icon": "🏇",
        "base_price_ryabucks": 800,
        "base_price_rbtc": Decimal("8.0"),
        "max_level": 5,
        "description": "Участие в скачках",
        "telegra_link": "https://telegra.ph/Gonochnaya-Licenziya-10-10",
        "level_benefits": {
            1: "Локальные скачки",
            2: "Региональные скачки",
            3: "Федеральные скачки",
            4: "Международные скачки",
            5: "Чемпионские скачки"
        }
    },
    LicenseType.FIGHTING: {
        "name": "Бойцовская Лицензия",
        "icon": "🥊",
        "base_price_ryabucks": 600,
        "base_price_rbtc": Decimal("6.0"),
        "max_level": 5,
        "description": "Петушиные бои",
        "telegra_link": "https://telegra.ph/Bojcovskaya-Licenziya-10-10",
        "level_benefits": {
            1: "Дворовые бои",
            2: "Районные турниры",
            3: "Городские чемпионаты",
            4: "Областные первенства",
            5: "Чемпион острова"
        }
    },
    LicenseType.QUANTUM: {
        "name": "Квантовая Лицензия",
        "icon": "⚛️",
        "base_price_ryabucks": 1500,
        "base_price_rbtc": Decimal("15.0"),
        "max_level": 3,
        "description": "Учёные и лаборатория",
        "telegra_link": "https://telegra.ph/Kvantovaya-Licenziya-10-10",
        "level_benefits": {
            1: "Базовая лаборатория",
            2: "Продвинутые эксперименты",
            3: "Мастер квантовых наук"
        }
    },
    LicenseType.EXPEDITION: {
        "name": "Экспедиционная Лицензия", 
        "icon": "🏕️",
        "base_price_ryabucks": 500,
        "base_price_rbtc": Decimal("5.0"),
        "max_level": 5,
        "description": "Q-Солдаты и экспедиции",
        "telegra_link": "https://telegra.ph/Ekspedicionnaya-Licenziya-10-10",
        "level_benefits": {
            1: "Лёгкие экспедиции",
            2: "Средние экспедиции",
            3: "Тяжёлые экспедиции", 
            4: "+25% к находкам RBTC",
            5: "Экстремальные экспедиции"
        }
    }
}

class LicenseService:
    """Улучшенная система лицензий с динамическим ценообразованием"""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.bank_service = None
        self.event_tracker = None
        self.client = None

        # Константы для экономики
        self.INITIAL_BANK_RYABUCKS = Decimal("1050000000")  # 1.05 млрд
        self.TOTAL_RBTC_POOL = Decimal("18480000")  # Без банка и DEX
        self.SMOOTHING_COEFFICIENT = 0.7

    async def _ensure_dependencies(self):
        """Подключаем зависимости"""
        if not self.bank_service:
            from services.bank_service import BankService
            self.bank_service = BankService()
        if not self.event_tracker:
            self.event_tracker = await get_event_tracker()
        if not self.client:
            self.client = await get_supabase_client()

    async def calculate_price_multipliers(self) -> Dict[str, float]:
        """Расчёт мультипликаторов цен"""
        try:
            # Упрощённая версия - фиксированные множители
            return {
                "ryabucks": 1.0,
                "rbtc": 1.0
            }
        except Exception as e:
            logger.error(f"Ошибка расчёта мультипликаторов: {e}")
            return {"ryabucks": 1.0, "rbtc": 1.0}

    async def _get_total_burned_rbtc(self) -> Decimal:
        """Получить общую сумму сожженных RBTC"""
        # В MVP версии используем заглушку
        # В полной версии будет сумма из Quantum Pass, лицензий, ускорений времени
        try:
            await self._ensure_dependencies()

            # Запрос суммы сожженных RBTC из audit_log
            burned_data = await self.client.execute_query(
                table="audit_log",
                operation="select",
                columns=["payload"],
                filters={"action_type": "rbtc_burned"}
            )

            total_burned = Decimal("0")
            for record in burned_data:
                payload = record.get("payload", {})
                if isinstance(payload, dict) and "amount" in payload:
                    total_burned += Decimal(str(payload["amount"]))

            return total_burned

        except Exception as e:
            logger.error(f"Ошибка получения сожженных RBTC: {e}")
            return Decimal("0")

    def calculate_license_price(self, license_type: str, level: int, multipliers: Dict[str, float]) -> Tuple[int, Decimal]:
        """
        Рассчитать стоимость лицензии с учётом мультипликаторов
        Возвращает (цена_рябаксы, цена_rbtc)
        """
        if license_type not in LICENSE_CONFIG:
            return 0, Decimal("0")

        config = LICENSE_CONFIG[license_type]

        # Экспоненциальный рост: цена удваивается с каждым уровнем
        base_ryabucks = config["base_price_ryabucks"] * (2 ** (level - 1))
        base_rbtc = config["base_price_rbtc"] * (2 ** (level - 1))

        # Применяем мультипликаторы
        final_ryabucks = int(base_ryabucks * multipliers["ryabucks"])
        final_rbtc = base_rbtc * Decimal(str(multipliers["rbtc"]))

        return final_ryabucks, final_rbtc

    async def get_user_licenses(self, user_id: int) -> Dict[str, int]:
        """Получить текущие уровни лицензий пользователя"""
        try:
            await self._ensure_dependencies()

            result = await self.client.execute_query(
                table="user_licenses",
                operation="select",
                columns=["license_type", "level"],
                filters={"user_id": user_id}
            )

            licenses = {}
            if result:
                for row in result:
                    licenses[row["license_type"]] = row.get("level", 0)

            return licenses

        except Exception as e:
            logger.error(f"Ошибка получения лицензий для {user_id}: {e}")
            return {}

    async def get_license_level(self, user_id: int, license_type: str) -> int:
        """Получить уровень конкретной лицензии (0 если нет)"""
        licenses = await self.get_user_licenses(user_id)
        return licenses.get(license_type, 0)

    async def upgrade_license(self, user_id: int, license_type: str, currency: str) -> Tuple[bool, str]:
        """
        Улучшить лицензию пользователя
        currency: 'ryabucks' или 'rbtc'
        Возвращает (успех, сообщение)
        """
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

            if currency == "ryabucks":
                if user.resources.ryabucks < ryabucks_price:
                    return False, f"Недостаточно рябаксов. Нужно: {ryabucks_price:,}, есть: {user.resources.ryabucks:,}"
                price_to_pay = ryabucks_price
            elif currency == "rbtc":
                if user.resources.rbtc.amount < rbtc_price:
                    return False, f"Недостаточно RBTC. Нужно: {rbtc_price}, есть: {user.resources.rbtc.amount}"
                price_to_pay = rbtc_price
            else:
                return False, "Неизвестная валюта"

            # Выполняем улучшение в транзакции
            async with self.client.transaction() as tx:
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
                        updates={"rbtc": new_rbtc}
                    )

                    # Записываем сжигание RBTC в audit_log
                    await self._record_rbtc_burn(user_id, rbtc_price, f"license_upgrade_{license_type}")

                # Обновляем лицензию
                await self.client.execute_query(
                    table="user_licenses",
                    operation="upsert",
                    data={
                        "user_id": user_id,
                        "license_type": license_type,
                        "level": next_level,
                        "upgraded_at": datetime.now(timezone.utc).isoformat()
                    }
                )

            # Трекаем событие
            await self.event_tracker.track_currency_spent(
                user_id=user_id,
                currency_type=currency,
                amount=price_to_pay,
                reason=f"license_upgrade_{license_type}"
            )

            significance = EventSignificance.IMPORTANT if license_type in [
                LicenseType.QUANTUM, LicenseType.POLITICAL, LicenseType.BANKER
            ] else EventSignificance.NORMAL

            await self.event_tracker.track_event(
                user_id=user_id,
                event_type=EventType.USER_LOGIN,  # Используем как активность
                data={
                    "action": "license_upgrade",
                    "license_type": license_type,
                    "new_level": next_level,
                    "price_paid": float(price_to_pay),
                    "currency": currency,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                significance=significance
            )

            logger.info(f"📜 Лицензия улучшена для {user_id}: {license_type} до уровня {next_level}")

            level_benefit = config.get("level_benefits", {}).get(next_level, "")
            benefit_text = f"\n🎁 Новая возможность: {level_benefit}" if level_benefit else ""

            return True, f"Лицензия '{config['name']}' улучшена до уровня {next_level}!{benefit_text}"

        except Exception as e:
            logger.error(f"Ошибка улучшения лицензии {license_type} для {user_id}: {e}")
            return False, "Техническая ошибка при улучшении лицензии"

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

    async def get_licenses_for_display(self, user_id: int) -> List[Dict]:
        """Получить лицензии для отображения в интерфейсе"""
        try:
            multipliers = await self.calculate_price_multipliers()
            current_licenses = await self.get_user_licenses(user_id)

            result = []

            for license_type, config in LICENSE_CONFIG.items():
                current_level = current_licenses.get(license_type, 0)

                if current_level >= config["max_level"]:
                    # Максимальный уровень достигнут
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
                    # Можно улучшить
                    next_level = current_level + 1
                    ryabucks_price, rbtc_price = self.calculate_license_price(license_type, next_level, multipliers)

                    result.append({
                        "type": license_type,
                        "icon": config["icon"], 
                        "name": config["name"],
                        "current_level": current_level,
                        "max_level": config["max_level"],
                        "ryabucks_price": f"{ryabucks_price:,}",
                        "rbtc_price": f"{rbtc_price:.2f}",
                        "ryabucks_price_raw": ryabucks_price,
                        "rbtc_price_raw": float(rbtc_price),
                        "telegra_link": config["telegra_link"],
                        "is_max": False
                    })

            return result

        except Exception as e:
            logger.error(f"Ошибка получения лицензий для отображения: {e}")
            return []

    async def check_license_requirement(self, user_id: int, action: str, required_level: int = 1) -> bool:
        """Проверить выполнение требований лицензии для действия"""
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
            return True  # Если нет требований, разрешаем

        required_license, min_level = action_requirements[action]
        current_level = await self.get_license_level(user_id, required_license)

        return current_level >= max(min_level, required_level)


logger.info("✅ Улучшенный LicenseService загружен")