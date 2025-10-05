# interfaces/telegram_bot/handlers/start.py
"""
Стартовый handler с выбором языка и системой заданий
"""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core.domain.entities import TutorialStep, Language
from config.texts import *
from config.game_stats import game_stats
from services.tutorial_service import tutorial_service
from services.quest_service import quest_service
from adapters.database.supabase.client import get_supabase_client

router = Router()
logger = logging.getLogger(__name__)


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_LANGUAGE_RU, callback_data="lang_ru")],
        [InlineKeyboardButton(text=BTN_LANGUAGE_EN, callback_data="lang_en")]
    ])


def get_start_menu() -> ReplyKeyboardMarkup:
    """Стартовое меню (вне острова)"""
    keyboard = [
        [KeyboardButton(text=BTN_ENTER_ISLAND)],
        [KeyboardButton(text=BTN_SETTINGS), KeyboardButton(text=BTN_SUPPORT)]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder=PLACEHOLDER_MENU
    )


def get_island_menu() -> ReplyKeyboardMarkup:
    """Меню острова"""
    keyboard = [
        [KeyboardButton(text=BTN_FARM), KeyboardButton(text=BTN_TOWN)],
        [KeyboardButton(text=BTN_CITIZEN), KeyboardButton(text=BTN_WORK)],
        [KeyboardButton(text=BTN_INVENTORY), KeyboardButton(text=BTN_FRIENDS)],
        [KeyboardButton(text=BTN_LEADERBOARD), KeyboardButton(text=BTN_OTHER)],
        [KeyboardButton(text=BTN_LEAVE_ISLAND)]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder=PLACEHOLDER_MENU
    )


async def format_welcome_message(stats: dict) -> str:
    """Форматирование стартового сообщения"""
    uptime = stats['uptime']

    if uptime['days'] > 0:
        uptime_text = f"{uptime['days']}д {uptime['hours']}ч {uptime['minutes']}м"
    else:
        uptime_text = f"{uptime['hours']}ч {uptime['minutes']}м"

    return WELCOME_TO_ISLAND.format(
        uptime=uptime_text,
        total_users=stats['total_users'],
        online_users=stats['online_users'],
        new_today=stats['new_users_today'],
        new_month=stats['new_users_month'],
        qpass_holders=stats['quantum_pass_holders']
    )


# === КОМАНДА /START ===

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"

        logger.info(f"👤 /start от {user_id} (@{username})")

        # Получаем клиент
        client = await get_supabase_client()

        # Проверяем пользователя
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["user_id", "tutorial_step", "has_island_access", "has_employer_license"],
            filters={"user_id": user_id},
            single=True
        )

        # Если пользователя нет - создаем
        if not user_data:
            await client.execute_query(
                table="users",
                operation="insert",
                data={
                    "user_id": user_id,
                    "username": username,
                    "ryabucks": 100,
                    "golden_shards": 1,
                    "tutorial_step": "not_started"
                }
            )
            user_data = {"tutorial_step": "not_started", "has_island_access": False}

        tutorial_step = TutorialStep(user_data['tutorial_step'])

        # Если туториал не начат - выбор языка
        if tutorial_step == TutorialStep.NOT_STARTED:
            await message.answer(
                LANGUAGE_SELECTION_TITLE,
                reply_markup=get_language_keyboard()
            )
            return

        # Если туториал в процессе
        if tutorial_step not in [TutorialStep.COMPLETED, TutorialStep.ISLAND_ACCESS_GRANTED]:
            hint = tutorial_service.get_next_step_hint(tutorial_step)
            await message.answer(f"🎯 Туториал в процессе\n\n{hint}")
            return

        # Показываем стартовое меню
        stats = await game_stats.get_all_stats()
        welcome_text = await format_welcome_message(stats)

        await message.answer(
            welcome_text,
            reply_markup=get_start_menu()
        )

    except Exception as e:
        logger.error(f"❌ Ошибка /start: {e}", exc_info=True)
        await message.answer(ERROR_GENERAL)


# === ВЫБОР ЯЗЫКА ===

@router.callback_query(F.data.startswith("lang_"))
async def select_language(callback: CallbackQuery):
    """Выбор языка"""
    try:
        user_id = callback.from_user.id
        lang_code = callback.data.split("_")[1]

        client = await get_supabase_client()
        await client.execute_query(
            table="users",
            operation="update",
            data={
                "language": lang_code,
                "tutorial_step": TutorialStep.CHARACTER_CREATION.value
            },
            filters={"user_id": user_id}
        )

        if lang_code == "ru":
            await callback.message.edit_text(LANGUAGE_SELECTED_RU, reply_markup=None)
        else:
            await callback.message.edit_text(LANGUAGE_SELECTED_EN, reply_markup=None)

        # Показываем создание персонажа
        from .tutorial import get_character_keyboard
        await callback.message.answer(
            CHARACTER_CREATION_TITLE,
            reply_markup=get_character_keyboard()
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка выбора языка: {e}")
        await callback.answer("Ошибка", show_alert=True)


# === ВХОД НА ОСТРОВ ===

@router.message(F.text == BTN_ENTER_ISLAND)
async def enter_island(message: Message, state: FSMContext):
    """Вход на остров - ИСПРАВЛЕННЫЙ"""
    try:
        user_id = message.from_user.id

        logger.info(f"🏝 Попытка входа на остров: {user_id}")

        # Получаем данные пользователя
        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["tutorial_step", "has_island_access", "has_employer_license", "ryabucks", "rbtc", "energy",
                     "energy_max", "level", "experience", "username"],
            filters={"user_id": user_id},
            single=True
        )

        if not user_data:
            logger.error(f"❌ Пользователь {user_id} не найден")
            await message.answer("❌ Пользователь не найден")
            return

        logger.info(
            f"📊 has_island_access={user_data.get('has_island_access')}, has_employer_license={user_data.get('has_employer_license')}")

        # Проверяем доступ
        if not user_data.get('has_island_access', False) and not user_data.get('has_employer_license', False):
            logger.warning(f"⚠️ Нет доступа для {user_id}")
            await message.answer("🎯 Сначала завершите туториал!")
            return

        logger.info(f"✅ Доступ разрешен")

        # Формируем меню и текст
        island_text = f"""
🏝️ Остров Ryabot

Добро пожаловать, {user_data.get('username', 'Островитянин')}!
🆙 Уровень: {user_data.get('level', 1)} | 📊 Опыт: {user_data.get('experience', 0)}

💰 Ресурсы:
💵 Рябаксы: {user_data.get('ryabucks', 0):,}
💠 RBTC: {user_data.get('rbtc', 0):.4f}
⚡ Энергия: {user_data.get('energy', 30)}/{user_data.get('energy_max', 30)}

🎮 Выберите действие:
"""

        await message.answer(
            island_text,
            reply_markup=get_island_menu()
        )

        logger.info(f"✅ Успешный вход на остров для {user_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка входа: {e}", exc_info=True)
        await message.answer(ERROR_ENTER_ISLAND)


# === ВЫХОД С ОСТРОВА ===

@router.message(F.text == BTN_LEAVE_ISLAND)
async def leave_island(message: Message, state: FSMContext):
    """Выход с острова"""
    try:
        stats = await game_stats.get_all_stats()
        welcome_text = await format_welcome_message(stats)

        await message.answer(
            welcome_text,
            reply_markup=get_start_menu()
        )

    except Exception as e:
        logger.error(f"❌ Ошибка выхода: {e}")
        await message.answer(ERROR_GENERAL)


# === ЖИТЕЛЬ ===

@router.message(F.text == BTN_CITIZEN)
async def citizen_menu(message: Message):
    """Меню жителя"""
    try:
        user_id = message.from_user.id

        current_quest = await quest_service.get_current_quest(user_id)

        if current_quest:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_CITIZEN_QUESTS, callback_data="citizen_quests")],
                [InlineKeyboardButton(text=BTN_CITIZEN_PROFILE, callback_data="citizen_profile")]
            ])

            quest_text = f"""
👤 ЖИТЕЛЬ ОСТРОВА

📋 Текущее задание:
{current_quest['title']}

{current_quest['description']}

💡 Как выполнить:
{current_quest['instruction']}

🎁 {current_quest['reward_text']}
            """.strip()
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_CITIZEN_PROFILE, callback_data="citizen_profile")]
            ])
            quest_text = "👤 ЖИТЕЛЬ ОСТРОВА\n\n🎉 Все задания выполнены!"

        await message.answer(quest_text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"❌ Ошибка меню жителя: {e}")
        await message.answer(ERROR_GENERAL)


# === ЗАГЛУШКИ ===

@router.message(F.text == BTN_FARM)
async def farm_menu(message: Message):
    await message.answer(f"🐔 ФЕРМА\n\n{SECTION_UNDER_DEVELOPMENT}")


@router.message(F.text == BTN_WORK)
async def work_menu(message: Message):
    try:
        from .work import show_work_menu
        await show_work_menu(message)
    except Exception as e:
        logger.error(f"Ошибка работ: {e}")
        await message.answer(ERROR_GENERAL)


@router.message(F.text == BTN_INVENTORY)
async def inventory_menu(message: Message):
    await message.answer(f"🎒 ИНВЕНТАРЬ\n\n{SECTION_UNDER_DEVELOPMENT}")


@router.message(F.text == BTN_FRIENDS)
async def friends_menu(message: Message):
    await message.answer(f"👥 ДРУЗЬЯ\n\n{SECTION_UNDER_DEVELOPMENT}")


@router.message(F.text == BTN_LEADERBOARD)
async def leaderboard_menu(message: Message):
    await message.answer(f"🏆 РЕЙТИНГ\n\n{SECTION_UNDER_DEVELOPMENT}")


@router.message(F.text == BTN_OTHER)
async def other_menu(message: Message):
    await message.answer(f"📋 ЕЩЁ\n\n{SECTION_UNDER_DEVELOPMENT}")


@router.message(F.text == BTN_SETTINGS)
async def settings_menu(message: Message):
    await message.answer(f"⚙️ НАСТРОЙКИ\n\n{SECTION_UNDER_DEVELOPMENT}")


@router.message(F.text == BTN_SUPPORT)
async def support_menu(message: Message):
    await message.answer(f"🆘 ПОДДЕРЖКА\n\n{SECTION_UNDER_DEVELOPMENT}")


@router.message(F.text == BTN_TOWN)
async def town_menu(message: Message):
    try:
        from .town import show_town_menu
        await show_town_menu(message)
    except Exception as e:
        logger.error(f"Ошибка города: {e}")
        await message.answer(ERROR_GENERAL)
