# interfaces/telegram_bot/handlers/start.py
"""
Главный handler с новой структурой меню + сохранением туториала
"""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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
        input_field_placeholder="Выберите действие"
    )


def get_island_menu() -> ReplyKeyboardMarkup:
    """Главное меню острова - ФИНАЛЬНЫЕ НАЗВАНИЯ (БЕЗ кнопки выхода)"""
    keyboard = [
        [KeyboardButton(text=BTN_FARM), KeyboardButton(text=BTN_TOWN)],
        [KeyboardButton(text=BTN_CITIZEN), KeyboardButton(text=BTN_WORK)],
        [KeyboardButton(text=BTN_INVENTORY), KeyboardButton(text=BTN_FRIENDS)],
        [KeyboardButton(text=BTN_LEADERBOARD), KeyboardButton(text=BTN_OTHER)]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите раздел острова"
    )


def get_stats_keyboard(selected: str = "rbtc") -> InlineKeyboardMarkup:
    """Инлайн кнопки статистики - переключение эмодзи пальца"""
    keyboard_data = {
        "rbtc": ["👉📊💠", "📊🏡", "📊🏢", "📊💼"],
        "farm": ["📊💠", "👉📊🏡", "📊🏢", "📊💼"],
        "city": ["📊💠", "📊🏡", "👉📊🏢", "📊💼"],
        "work": ["📊💠", "📊🏡", "📊🏢", "👉📊💼"]
    }

    buttons = keyboard_data.get(selected, keyboard_data["rbtc"])

    keyboard = [
        [
            InlineKeyboardButton(text=buttons[0], callback_data="stats_rbtc"),
            InlineKeyboardButton(text=buttons[1], callback_data="stats_farm"),
            InlineKeyboardButton(text=buttons[2], callback_data="stats_city"),
            InlineKeyboardButton(text=buttons[3], callback_data="stats_work")
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_island_stats() -> dict:
    """Получить статистику острова для главного меню"""
    # TODO: Получать реальные данные из БД
    return {
        "total_rbtc_mined": 0,
        "quantum_labs": 0,
        "friends_total": 0,
        "expeditions_total": 0,
        "anomalies_total": 0,
        "fights_total": 0,
        "races_total": 0,
        "boxes_total": 0
    }


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

        # Если туториал в процессе (до доступа к острову)
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
    """Вход на остров - показываем новое меню со статистикой"""
    try:
        user_id = message.from_user.id

        logger.info(f"🏝 Попытка входа на остров: {user_id}")

        # Получаем данные пользователя
        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["tutorial_step", "has_island_access", "has_employer_license"],
            filters={"user_id": user_id},
            single=True
        )

        if not user_data:
            logger.error(f"❌ Пользователь {user_id} не найден")
            await message.answer("❌ Пользователь не найден")
            return

        # Проверяем доступ
        if not user_data.get('has_island_access', False) and not user_data.get('has_employer_license', False):
            logger.warning(f"⚠️ Нет доступа для {user_id}")
            await message.answer("🎯 Сначала завершите туториал!")
            return

        logger.info(f"✅ Доступ разрешен для {user_id}")

        # Показываем НОВОЕ меню со статистикой
        stats = await get_island_stats()
        menu_text = ISLAND_MAIN_MENU.format(**stats)

        # Отправляем инлайн меню со статистикой
        await message.answer(
            menu_text,
            reply_markup=get_stats_keyboard("rbtc")
        )

        # Отправляем нижнее меню
        await message.answer(
            "🏝 Выберите раздел:",
            reply_markup=get_island_menu()
        )

        logger.info(f"✅ Успешный вход на остров для {user_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка входа: {e}", exc_info=True)
        await message.answer(ERROR_ENTER_ISLAND)


# === ОБРАБОТЧИКИ СТАТИСТИКИ ===

@router.callback_query(F.data.startswith("stats_"))
async def handle_stats(callback: CallbackQuery):
    """Обработка переключения статистики"""
    try:
        stats_type = callback.data.split("_")[1]

        # Получаем статистику
        stats = await get_island_stats()
        menu_text = ISLAND_MAIN_MENU.format(**stats)

        # Обновляем с новыми кнопками (палец переместился)
        await callback.message.edit_text(
            menu_text,
            reply_markup=get_stats_keyboard(stats_type)
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка статистики: {e}")
        await callback.answer("Ошибка", show_alert=True)


# === ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ===

@router.message(F.text == BTN_TOWN)
async def town_menu(message: Message):
    """Меню города"""
    try:
        from .town import show_town_menu
        await show_town_menu(message)
    except Exception as e:
        logger.error(f"❌ Ошибка города: {e}")
        await message.answer(ERROR_GENERAL)


@router.message(F.text == BTN_WORK)
async def work_menu(message: Message):
    """Меню работ"""
    try:
        from .work import show_work_menu
        await show_work_menu(message)
    except Exception as e:
        logger.error(f"❌ Ошибка работ: {e}")
        await message.answer(ERROR_GENERAL)


@router.message(F.text == BTN_CITIZEN)
async def citizen_menu(message: Message):
    """Меню жителя - переадресуем в отдельный handler"""
    try:
        from .citizen import show_citizen_menu
        await show_citizen_menu(message)
    except Exception as e:
        logger.error(f"❌ Ошибка жителя: {e}")
        await message.answer(ERROR_GENERAL)


@router.message(F.text == BTN_FARM)
async def farm_menu(message: Message):
    """Меню фермы"""
    try:
        from .farm import show_farm_menu
        await show_farm_menu(message)
    except Exception as e:
        logger.error(f"❌ Ошибка фермы: {e}")
        await message.answer(ERROR_GENERAL)


@router.message(F.text == BTN_INVENTORY)
async def inventory_menu(message: Message):
    """Меню рюкзака"""
    try:
        from .inventory import show_inventory_menu
        await show_inventory_menu(message)
    except Exception as e:
        logger.error(f"❌ Ошибка рюкзака: {e}")
        await message.answer(ERROR_GENERAL)


@router.message(F.text == BTN_FRIENDS)
async def friends_menu(message: Message):
    """Меню друзей"""
    try:
        from .friends import show_friends_menu
        await show_friends_menu(message)
    except Exception as e:
        logger.error(f"❌ Ошибка друзей: {e}")
        await message.answer(ERROR_GENERAL)


@router.message(F.text == BTN_LEADERBOARD)
async def leaderboard_menu(message: Message):
    """Меню лидерборда"""
    try:
        from .leaderboard import show_leaderboard_menu
        await show_leaderboard_menu(message)
    except Exception as e:
        logger.error(f"❌ Ошибка лидерборда: {e}")
        await message.answer(ERROR_GENERAL)


@router.message(F.text == BTN_OTHER)
async def other_menu(message: Message):
    """Меню прочего"""
    try:
        from .other import show_other_menu
        await show_other_menu(message)
    except Exception as e:
        logger.error(f"❌ Ошибка прочего: {e}")
        await message.answer(ERROR_GENERAL)


# === СТАРЫЕ КНОПКИ ДЛЯ СОВМЕСТИМОСТИ ===

@router.message(F.text == BTN_SETTINGS)
async def settings_menu(message: Message):
    """Настройки"""
    await message.answer(f"⚙️ *НАСТРОЙКИ*\n\n{SECTION_UNDER_DEVELOPMENT}")


@router.message(F.text == BTN_SUPPORT)
async def support_menu(message: Message):
    """Поддержка"""
    await message.answer(f"🆘 *ПОДДЕРЖКА*\n\n{SECTION_UNDER_DEVELOPMENT}")
