# interfaces/telegram_bot/handlers/town_hall.py
"""
Town Hall Handler - обработчики для ратуши и лицензий
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.license_service import LicenseService, LICENSE_CONFIG
from services.energy_service import EnergyService
from adapters.database.supabase.repositories.user_repository import SupabaseUserRepository
from adapters.database.supabase.client import get_supabase_client
from config.texts import TOWN_HALL_TEXTS

logger = logging.getLogger(__name__)
router = Router(name="town_hall")

# Инициализируем сервисы
_license_service = None
_energy_service = None

async def get_license_service() -> LicenseService:
    """Получить экземпляр LicenseService"""
    global _license_service
    if not _license_service:
        client = await get_supabase_client()
        user_repo = SupabaseUserRepository(client)
        _license_service = LicenseService(user_repo)
    return _license_service

async def get_energy_service() -> EnergyService:
    """Получить экземпляр EnergyService"""
    global _energy_service
    if not _energy_service:
        client = await get_supabase_client()
        user_repo = SupabaseUserRepository(client)
        _energy_service = EnergyService(user_repo)
    return _energy_service

@router.callback_query(F.data == "town_hall")
async def show_town_hall(query: CallbackQuery):
    """Показать главное меню ратуши"""
    try:
        user_id = query.from_user.id
        energy_service = await get_energy_service()

        # Получаем информацию об энергии
        energy_info = await energy_service.get_energy_info(user_id)
        current_energy = energy_info["current"] if energy_info else "N/A"

        # Формируем текст
        text = f"""〰️〰️ 🏛 РАТУША ℹ️ [🔋{current_energy}] 〰️〰️

«Суровое сердце острова Рябот, где судьбы вершатся с помощью печатей на документах. Здесь выдаются лицензии, взимаются налоги, а амбициозные фермеры отстаивают свои интересы»."""

        # Создаём клавиатуру
        keyboard = InlineKeyboardBuilder()

        # Первая строка - Мой Кабинет
        keyboard.add(InlineKeyboardButton(
            text="🚪 Мой Кабинет",
            callback_data="my_office"
        ))

        # Вторая строка - Лицензии и Поручения
        keyboard.row(
            InlineKeyboardButton(text="📜 Лицензии", callback_data="licenses"),
            InlineKeyboardButton(text="🔖 Поручения", callback_data="tasks")
        )

        # Третья строка - Награды и Гильдии
        keyboard.row(
            InlineKeyboardButton(text="🎁 Награды", callback_data="rewards"),
            InlineKeyboardButton(text="🏰 Гильдии", callback_data="guilds")
        )

        # Четвертая строка - Бонусы и Назад
        keyboard.row(
            InlineKeyboardButton(text="📆 Бонусы", callback_data="daily_bonuses"),
            InlineKeyboardButton(text="↪️ Назад", callback_data="main_menu")
        )

        await query.message.edit_text(text, reply_markup=keyboard.as_markup())
        await query.answer()

    except Exception as e:
        logger.error(f"Ошибка показа ратуши для {query.from_user.id}: {e}")
        await query.answer("Техническая ошибка", show_alert=True)

@router.callback_query(F.data == "licenses")
async def show_licenses(query: CallbackQuery):
    """Показать меню лицензий"""
    try:
        user_id = query.from_user.id
        license_service = await get_license_service()

        # Получаем лицензии для отображения
        licenses_data = await license_service.get_licenses_for_display(user_id)

        # Получаем мультипликаторы для информации
        multipliers = await license_service.calculate_price_multipliers()

        # Формируем текст
        text = f"""〰️ 📜 БЮРО ЛИЦЕНЗИЙ ℹ️ 〰️

«Суровый клерк просматривает стопку бумаг, держа наготове золотые печати. Каждое разрешение открывает новые возможности — за определённую цену».

💰 Мультипликатор рябаксов: x{multipliers['ryabucks']}
⚛️ Мультипликатор RBTC: x{multipliers['rbtc']}"""

        # Создаём клавиатуру
        keyboard = InlineKeyboardBuilder()

        # Добавляем лицензии по 3 кнопки в ряд (гайд | рябаксы | RBTC)
        for license_data in licenses_data:
            # Первая кнопка - ссылка на гайд
            keyboard.add(InlineKeyboardButton(
                text=f"{license_data['icon']} Ур.{license_data['current_level']}",
                url=license_data['telegra_link']
            ))

            # Вторая кнопка - цена в рябаксах
            ryabucks_text = f"💵 {license_data['ryabucks_price']}"
            keyboard.add(InlineKeyboardButton(
                text=ryabucks_text,
                callback_data=f"buy_license:{license_data['type']}:ryabucks" if not license_data['is_max'] else "license_maxed"
            ))

            # Третья кнопка - цена в RBTC
            rbtc_text = f"💠 {license_data['rbtc_price']}"
            keyboard.add(InlineKeyboardButton(
                text=rbtc_text,
                callback_data=f"buy_license:{license_data['type']}:rbtc" if not license_data['is_max'] else "license_maxed"
            ))

            # Переход на новую строку после каждой лицензии
            keyboard.adjust(3)

        # Кнопка назад
        keyboard.row(InlineKeyboardButton(text="↪️ Назад", callback_data="town_hall"))

        await query.message.edit_text(text, reply_markup=keyboard.as_markup())
        await query.answer()

    except Exception as e:
        logger.error(f"Ошибка показа лицензий для {query.from_user.id}: {e}")
        await query.answer("Техническая ошибка", show_alert=True)

@router.callback_query(F.data.startswith("buy_license:"))
async def buy_license(query: CallbackQuery):
    """Покупка лицензии"""
    try:
        # Парсим callback_data
        _, license_type, currency = query.data.split(":")
        user_id = query.from_user.id

        license_service = await get_license_service()

        # Пытаемся купить лицензию
        success, message = await license_service.upgrade_license(user_id, license_type, currency)

        if success:
            # Успешная покупка
            await query.answer(message, show_alert=True)

            # Обновляем интерфейс лицензий
            await show_licenses(query)
        else:
            # Ошибка покупки
            await query.answer(message, show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка покупки лицензии для {query.from_user.id}: {e}")
        await query.answer("Техническая ошибка при покупке лицензии", show_alert=True)

@router.callback_query(F.data == "license_maxed")
async def license_maxed_notification(query: CallbackQuery):
    """Уведомление о максимальной лицензии"""
    await query.answer("Лицензия уже максимального уровня! 🎉", show_alert=True)

@router.callback_query(F.data == "my_office")
async def show_my_office(query: CallbackQuery):
    """Заглушка для личного кабинета"""
    await query.answer("🚧 Личный кабинет в разработке", show_alert=True)

@router.callback_query(F.data == "tasks")
async def show_tasks(query: CallbackQuery):
    """Заглушка для поручений"""
    await query.answer("🚧 Система поручений в разработке", show_alert=True)

@router.callback_query(F.data == "rewards")
async def show_rewards(query: CallbackQuery):
    """Заглушка для наград"""
    await query.answer("🚧 Система наград в разработке", show_alert=True)

@router.callback_query(F.data == "guilds")
async def show_guilds(query: CallbackQuery):
    """Заглушка для гильдий"""
    await query.answer("🚧 Система гильдий в разработке", show_alert=True)

@router.callback_query(F.data == "daily_bonuses")
async def show_daily_bonuses(query: CallbackQuery):
    """Заглушка для ежедневных бонусов"""
    await query.answer("🚧 Ежедневные бонусы в разработке", show_alert=True)

logger.info("✅ Town Hall handler загружен")