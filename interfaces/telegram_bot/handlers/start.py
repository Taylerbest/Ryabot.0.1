# interfaces/telegram_bot/handlers/start.py
"""
НОВЫЙ стартовый handler с правильным туториалом
"""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# Core imports
from core.use_cases.user.create_user import CreateUserUseCase, GetUserProfileUseCase, UpdateUserResourcesUseCase
from adapters.database.supabase.client import get_supabase_client
from adapters.database.supabase.repositories.user_repository import SupabaseUserRepository
from core.domain.entities import TutorialStep, CharacterPreset

# Config and services
from config.texts import *
from config.game_stats import game_stats
from services.tutorial_service import tutorial_service

router = Router()
logger = logging.getLogger(__name__)

async def get_user_use_cases():
    """Получить use cases"""
    client = await get_supabase_client()
    user_repo = SupabaseUserRepository(client)
    
    return {
        'create_user': CreateUserUseCase(user_repo),
        'get_profile': GetUserProfileUseCase(user_repo),
        'update_resources': UpdateUserResourcesUseCase(user_repo)
    }

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
    """Команда /start - проверяем туториал"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"
        
        logger.info(f"👤 Пользователь {user_id} (@{username}) запустил /start")
        
        # Создаем пользователя
        use_cases = await get_user_use_cases()
        user = await use_cases['create_user'].execute(user_id, username)
        
        if not user:
            await message.answer(ERROR_GENERAL)
            return
        
        # Проверяем туториал
        tutorial_step = await tutorial_service.get_tutorial_step(user_id)
        
        if tutorial_step == TutorialStep.NOT_STARTED:
            # Начинаем с создания персонажа
            from .tutorial import router as tutorial_router
            from .tutorial import start_character_creation
            
            # Создаем fake callback для запуска создания персонажа
            from aiogram.types import CallbackQuery, User
            fake_callback = CallbackQuery(
                id="start_char", 
                from_user=message.from_user,
                chat_instance="start",
                data="start_character_creation",
                message=message
            )
            
            await start_character_creation(fake_callback, state)
            return
        
        elif tutorial_step != TutorialStep.COMPLETED:
            # Продолжаем туториал
            hint = tutorial_service.get_next_step_hint(tutorial_step)
            await message.answer(f"🎯 **Туториал в процессе**\n\n{hint}")
            return
        
        # Туториал завершен - показываем стартовый экран
        stats = await game_stats.get_all_stats()
        welcome_text = await format_welcome_message(stats)
        
        await message.answer(
            welcome_text,
            reply_markup=get_start_menu()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка в /start для пользователя {message.from_user.id}: {e}")
        await message.answer(ERROR_GENERAL)

# === ВХОД НА ОСТРОВ ===

@router.message(F.text == BTN_ENTER_ISLAND)
async def enter_island(message: Message, state: FSMContext):
    """Вход на остров - ИСПРАВЛЕННЫЙ"""
    try:
        user_id = message.from_user.id
        
        # Проверяем туториал
        tutorial_step = await tutorial_service.get_tutorial_step(user_id)
        
        if tutorial_step != TutorialStep.COMPLETED:
            hint = tutorial_service.get_next_step_hint(tutorial_step)
            await message.answer(f"🎯 Сначала завершите туториал!\n\n{hint}")
            return
        
        # Получаем профиль
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)
        
        if not profile:
            await message.answer(ERROR_GENERAL)
            return
        
        # Формируем приветствие острова
        island_text = ISLAND_MENU.format(
            username=profile.get('username', 'Островитянин'),
            level=profile['level'],
            experience=profile['experience'],
            ryabucks=profile['ryabucks'],
            rbtc=f"{profile['rbtc']:.4f}",
            energy=profile['energy'],
            energy_max=profile['energy_max']
        )
        
        await message.answer(
            island_text,
            reply_markup=get_island_menu()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка входа на остров для {message.from_user.id}: {e}")
        await message.answer(ERROR_ENTER_ISLAND)

# === ВЫХОД С ОСТРОВА ===

@router.message(F.text == BTN_LEAVE_ISLAND)
async def leave_island(message: Message, state: FSMContext):
    """Выход с острова"""
    try:
        # Показываем стартовый экран
        stats = await game_stats.get_all_stats()
        welcome_text = await format_welcome_message(stats)
        
        await message.answer(
            welcome_text,
            reply_markup=get_start_menu()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка выхода с острова: {e}")
        await message.answer(ERROR_GENERAL)

# === ПРОФИЛЬ ЖИТЕЛЯ ===

@router.message(F.text == BTN_CITIZEN)
async def citizen_profile(message: Message):
    """Профиль жителя"""
    try:
        user_id = message.from_user.id
        
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)
        
        if not profile:
            await message.answer(ERROR_GENERAL)
            return
        
        # Получаем выбранного персонажа
        character_name = CHARACTER_NAMES.get(profile.get('character_preset', 1), "Неизвестный")
        
        profile_text = f"""
👤 **ПРОФИЛЬ ЖИТЕЛЯ**

🎭 **Персонаж:** {character_name}
🆔 **{profile['username']}** (ID: {profile['user_id']})
🆙 **Уровень {profile['level']}** | 📊 **Опыт:** {profile['experience']}

💰 **РЕСУРСЫ:**
💵 {profile['ryabucks']:,} рябаксов
💠 {profile['rbtc']:.4f} RBTC
⚡ {profile['energy']}/{profile['energy_max']} энергии
🧪 {profile['liquid_experience']} жидкого опыта
💎 {profile['golden_shards']} золотых осколков

📜 **ЛИЦЕНЗИИ:**
{"✅" if profile.get('has_employer_license') else "❌"} Работодатель
{"✅" if profile.get('has_farm_license') else "❌"} Фермер

🏝️ **Гражданин острова с** {profile['created_at'][:10]}
        """.strip()
        
        await message.answer(profile_text)
        
    except Exception as e:
        logger.error(f"❌ Ошибка профиля: {e}")
        await message.answer(ERROR_GENERAL)

# === ЗАГЛУШКИ РАЗДЕЛОВ ===

@router.message(F.text == BTN_FARM)
async def farm_menu(message: Message):
    """Ферма (заглушка)"""
    await message.answer(f"🐔 **ФЕРМА**\n\n{SECTION_UNDER_DEVELOPMENT}")

@router.message(F.text == BTN_WORK)
async def work_menu(message: Message):
    """Рябота (заглушка)"""
    await message.answer(f"💼 **РЯБОТА**\n\n{SECTION_UNDER_DEVELOPMENT}")

@router.message(F.text == BTN_INVENTORY)
async def inventory_menu(message: Message):
    """Инвентарь (заглушка)"""
    await message.answer(f"🎒 **ИНВЕНТАРЬ**\n\n{SECTION_UNDER_DEVELOPMENT}")

@router.message(F.text == BTN_FRIENDS)
async def friends_menu(message: Message):
    """Друзья (заглушка)"""
    await message.answer(f"👥 **ДРУЗЬЯ**\n\n{SECTION_UNDER_DEVELOPMENT}")

@router.message(F.text == BTN_LEADERBOARD)
async def leaderboard_menu(message: Message):
    """Рейтинг (заглушка)"""
    await message.answer(f"🏆 **РЕЙТИНГ**\n\n{SECTION_UNDER_DEVELOPMENT}")

@router.message(F.text == BTN_OTHER)
async def other_menu(message: Message):
    """Ещё (заглушка)"""
    await message.answer(f"📋 **ЕЩЁ**\n\n{SECTION_UNDER_DEVELOPMENT}")

@router.message(F.text == BTN_SETTINGS)
async def settings_menu(message: Message):
    """Настройки (заглушка)"""
    await message.answer(f"⚙️ **НАСТРОЙКИ**\n\n{SECTION_UNDER_DEVELOPMENT}")

@router.message(F.text == BTN_SUPPORT)
async def support_menu(message: Message):
    """Поддержка (заглушка)"""
    await message.answer(f"🆘 **ПОДДЕРЖКА**\n\n{SECTION_UNDER_DEVELOPMENT}")

# === ПЕРЕХОД В ГОРОД ===

@router.message(F.text == BTN_TOWN)
async def town_menu(message: Message):
    """Переход в город"""
    try:
        # Импортируем handler города
        from .town import show_town_menu
        await show_town_menu(message)
        
    except Exception as e:
        logger.error(f"❌ Ошибка города: {e}")
        await message.answer(ERROR_GENERAL)