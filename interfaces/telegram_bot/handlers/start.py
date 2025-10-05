# interfaces/telegram_bot/handlers/start.py
"""
Новый стартовый handler с выбором языка и системой заданий
"""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# Core imports
from core.use_cases.user.create_user import CreateUserUseCase, GetUserProfileUseCase, UpdateUserResourcesUseCase
from adapters.database.supabase.client import get_supabase_client
from adapters.database.supabase.repositories.user_repository import SupabaseUserRepository
from core.domain.entities import TutorialStep, Language

# Config and services
from config.texts import *
from config.game_stats import game_stats
from services.tutorial_service import tutorial_service
from services.quest_service import quest_service

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
    """Команда /start - начинаем с выбора языка"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"
        
        logger.info(f"👤 Пользователь {user_id} (@{username}) запустил /start")
        
        # Создаем пользователя (если не существует)
        use_cases = await get_user_use_cases()
        user = await use_cases['create_user'].execute(user_id, username)
        
        if not user:
            await message.answer(ERROR_GENERAL)
            return
        
        # Проверяем туториал
        tutorial_step = await tutorial_service.get_tutorial_step(user_id)
        
        if tutorial_step == TutorialStep.NOT_STARTED:
            # Начинаем с выбора языка
            await message.answer(
                LANGUAGE_SELECTION_TITLE,
                reply_markup=get_language_keyboard()
            )
            return
        
        elif tutorial_step in [
            TutorialStep.LANGUAGE_SELECTION,
            TutorialStep.CHARACTER_CREATION,
            TutorialStep.SHIPWRECK,
            TutorialStep.TAVERN_VISIT,
            TutorialStep.PAWN_SHOP,
            TutorialStep.TOWN_HALL_REGISTER,
            TutorialStep.EMPLOYER_LICENSE
        ]:
            # Туториал в процессе - направляем в tutorial handler
            hint = tutorial_service.get_next_step_hint(tutorial_step)
            await message.answer(f"🎯 *Туториал в процессе*\n\n{hint}")
            return
        
        elif tutorial_step != TutorialStep.COMPLETED:
            # Доступ к острову есть, но есть активные задания
            current_quest = await quest_service.get_current_quest(user_id)
            if current_quest:
                await message.answer(
                    f"🎯 *У вас есть активное задание!*\n\n"
                    f"📋 *{current_quest['title']}*\n"
                    f"{current_quest['description']}\n\n"
                    f"💡 {current_quest['instruction']}"
                )
            else:
                await message.answer("🎉 Все задания выполнены! Добро пожаловать на остров!")
                
        # Туториал завершен или доступ к острову есть - показываем стартовый экран
        stats = await game_stats.get_all_stats()
        welcome_text = await format_welcome_message(stats)
        
        await message.answer(
            welcome_text,
            reply_markup=get_start_menu()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка в /start для пользователя {message.from_user.id}: {e}")
        await message.answer(ERROR_GENERAL)

# === ВЫБОР ЯЗЫКА ===

@router.callback_query(F.data.startswith("lang_"))
async def select_language(callback: CallbackQuery):
    """Выбор языка"""
    try:
        user_id = callback.from_user.id
        lang_code = callback.data.split("_")[1]  # ru или en
        
        # Сохраняем язык в БД
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
        
        # Показываем подтверждение и переходим к созданию персонажа
        if lang_code == "ru":
            await callback.message.edit_text(
                LANGUAGE_SELECTED_RU,
                reply_markup=None
            )
        else:
            await callback.message.edit_text(
                LANGUAGE_SELECTED_EN, 
                reply_markup=None
            )
        
        # Сразу показываем создание персонажа
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
    """Вход на остров"""
    try:
        user_id = message.from_user.id
        
        # Проверяем доступ
        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["tutorial_step", "has_island_access", "tutorial_completed"],
            filters={"user_id": user_id},
            single=True
        )
        
        if not user_data:
            await message.answer(ERROR_GENERAL)
            return
        
        current_step = TutorialStep(user_data['tutorial_step'])
        
        # Проверяем доступ к острову
        if not user_data.get('has_island_access', False) and current_step not in [
            TutorialStep.ISLAND_ACCESS_GRANTED,
            TutorialStep.TASK_HIRE_WORKER,
            TutorialStep.TASK_FIRST_WORK,
            TutorialStep.TASK_CITIZEN_QUEST,
            TutorialStep.TASK_TRAIN_SPECIALIST,
            TutorialStep.TASK_BUY_FARM_LICENSE,
            TutorialStep.TASK_BUY_LAND,
            TutorialStep.TASK_BUILD_CROP_BED,
            TutorialStep.TASK_PLANT_GRAIN,
            TutorialStep.TASK_BUILD_HENHOUSE,
            TutorialStep.TASK_BUY_CHICKEN,
            TutorialStep.COMPLETED
        ]:
            hint = tutorial_service.get_next_step_hint(current_step)
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
        stats = await game_stats.get_all_stats()
        welcome_text = await format_welcome_message(stats)
        
        await message.answer(
            welcome_text,
            reply_markup=get_start_menu()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка выхода с острова: {e}")
        await message.answer(ERROR_GENERAL)

# === ЖИТЕЛЬ - СИСТЕМА ЗАДАНИЙ ===

@router.message(F.text == BTN_CITIZEN)
async def citizen_menu(message: Message):
    """Меню жителя с заданиями"""
    try:
        user_id = message.from_user.id
        
        # Получаем текущее задание
        current_quest = await quest_service.get_current_quest(user_id)
        
        if current_quest:
            # Есть активное задание
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_CITIZEN_QUESTS, callback_data="citizen_quests")],
                [InlineKeyboardButton(text=BTN_CITIZEN_PROFILE, callback_data="citizen_profile")],
                [InlineKeyboardButton(text=BTN_CITIZEN_ACHIEVEMENTS, callback_data="citizen_achievements")]
            ])
            
            quest_text = f"""
👤 *ЖИТЕЛЬ ОСТРОВА*

📋 *Текущее задание:*
*{current_quest['title']}*

{current_quest['description']}

💡 *Как выполнить:*
{current_quest['instruction']}

🎁 *{current_quest['reward_text']}*

👇 Выберите раздел:
            """.strip()
            
        else:
            # Заданий нет
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_CITIZEN_PROFILE, callback_data="citizen_profile")],
                [InlineKeyboardButton(text=BTN_CITIZEN_ACHIEVEMENTS, callback_data="citizen_achievements")]
            ])
            
            quest_text = f"""
👤 *ЖИТЕЛЬ ОСТРОВА*

🎉 *Все задания выполнены!*
Поздравляем с завершением обучения!

👇 Выберите раздел:
            """.strip()
        
        await message.answer(quest_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Ошибка меню жителя: {e}")
        await message.answer(ERROR_GENERAL)

# === ОБРАБОТЧИКИ МЕНЮ ЖИТЕЛЯ ===

@router.callback_query(F.data == "citizen_quests")
async def citizen_quests(callback: CallbackQuery):
    """Показать список заданий"""
    try:
        user_id = callback.from_user.id
        
        current_quest = await quest_service.get_current_quest(user_id)
        
        if current_quest:
            # Показываем текущее задание с кнопкой завершения (если это задание "Начало")
            if current_quest["quest_id"] == "citizen_quest":
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Получить опыт", callback_data="complete_citizen_quest")],
                    [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_citizen")]
                ])
            else:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_citizen")]
                ])
            
            text = f"""
📋 *АКТИВНЫЕ ЗАДАНИЯ*

*{current_quest['title']}*

{current_quest['description']}

💡 *Инструкция:*
{current_quest['instruction']}

🎁 *Награда:* {current_quest['reward_text']}
            """.strip()
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_citizen")]
            ])
            text = "🎉 Все задания выполнены!"
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка заданий: {e}")
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "complete_citizen_quest")
async def complete_citizen_quest(callback: CallbackQuery):
    """Завершить задание 'Начало'"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"
        
        # Проверяем, доступно ли это задание
        if not await quest_service.is_quest_available(user_id, "citizen_quest"):
            await callback.answer("Это задание сейчас недоступно", show_alert=True)
            return
        
        # Выдаем награды
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)
        
        await use_cases['update_resources'].execute(user_id, {
            "experience": profile['experience'] + 50,
            "liquid_experience": profile['liquid_experience'] + 10
        })
        
        # Логируем
        from services.blockchain_service import blockchain_service
        await blockchain_service.log_action(
            "QUEST_COMPLETED", user_id, username,
            {"quest": "citizen_quest", "reward_exp": 50, "reward_liquid_exp": 10},
            significance=0
        )
        
        # Завершаем задание
        await quest_service.complete_quest(user_id, "citizen_quest")
        
        # Показываем результат
        await callback.message.edit_text(
            f"""
✅ *ЗАДАНИЕ «НАЧАЛО» ВЫПОЛНЕНО!*

🎁 *Получено:*
📊 +50 опыта
🧪 +10 жидкого опыта

🎯 *Следующее задание:* Обучите рабочего на специалиста!
Идите в 🏘️ Город → 🎓 Академия → 🎓 Курсы экспертов
            """.strip(),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_citizen")]
            ])
        )
        
        await callback.answer("✅ Задание выполнено!", show_alert=True)
        
    except Exception as e:
        logger.error(f"Ошибка завершения задания: {e}")
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "citizen_profile") 
async def citizen_profile(callback: CallbackQuery):
    """Профиль жителя"""
    try:
        user_id = callback.from_user.id
        
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)
        
        if not profile:
            await callback.answer(ERROR_GENERAL, show_alert=True)
            return
        
        # Получаем выбранного персонажа
        character_name = CHARACTER_NAMES.get(profile.get('character_preset', 1), "Неизвестный")
        
        profile_text = f"""
👤 *ПРОФИЛЬ ЖИТЕЛЯ*

🎭 *Персонаж:* {character_name}
🆔 *{profile['username']}* (ID: {profile['user_id']})
🆙 *Уровень {profile['level']}* | 📊 *Опыт:* {profile['experience']}

💰 *РЕСУРСЫ:*
💵 {profile['ryabucks']:,} рябаксов
💠 {profile['rbtc']:.4f} RBTC
⚡ {profile['energy']}/{profile['energy_max']} энергии
🧪 {profile['liquid_experience']} жидкого опыта
💎 {profile['golden_shards']} золотых осколков

📜 *ЛИЦЕНЗИИ:*
{"✅" if profile.get('has_employer_license') else "❌"} Работодатель
{"✅" if profile.get('has_farm_license') else "❌"} Фермер

🏝️ *Гражданин острова с* {profile['created_at'][:10]}
        """.strip()
        
        await callback.message.edit_text(
            profile_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_citizen")]
            ])
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка профиля: {e}")
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "citizen_achievements")
async def citizen_achievements(callback: CallbackQuery):
    """Достижения (заглушка)"""
    await callback.message.edit_text(
        f"🏆 *ДОСТИЖЕНИЯ*\n\n{SECTION_UNDER_DEVELOPMENT}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_citizen")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_citizen")
async def back_to_citizen(callback: CallbackQuery):
    """Назад в меню жителя"""
    # Перезапускаем меню жителя
    from aiogram.types import Message
    fake_message = Message(
        message_id=callback.message.message_id,
        date=callback.message.date,
        chat=callback.message.chat,
        content_type='text',
        options={},
        text=BTN_CITIZEN
    )
    fake_message.from_user = callback.from_user
    fake_message.answer = callback.message.edit_text
    
    await citizen_menu(fake_message)

# === ЗАГЛУШКИ РАЗДЕЛОВ ===

@router.message(F.text == BTN_FARM)
async def farm_menu(message: Message):
    """Ферма"""
    user_id = message.from_user.id
    
    if await quest_service.can_access_feature(user_id, "farm"):
        await message.answer(f"🐔 *ФЕРМА*\n\n{SECTION_UNDER_DEVELOPMENT}")
    else:
        await message.answer(f"🐔 *ФЕРМА*\n\n{SECTION_LOCKED}")

@router.message(F.text == BTN_WORK)
async def work_menu(message: Message):
    """Рябота - показываем меню работ"""
    try:
        from .work import show_work_menu
        await show_work_menu(message)
    except Exception as e:
        logger.error(f"❌ Ошибка работ: {e}")
        await message.answer(ERROR_GENERAL)

@router.message(F.text == BTN_INVENTORY)
async def inventory_menu(message: Message):
    """Инвентарь"""
    await message.answer(f"🎒 *ИНВЕНТАРЬ*\n\n{SECTION_UNDER_DEVELOPMENT}")

@router.message(F.text == BTN_FRIENDS)
async def friends_menu(message: Message):
    """Друзья"""
    await message.answer(f"👥 *ДРУЗЬЯ*\n\n{SECTION_UNDER_DEVELOPMENT}")

@router.message(F.text == BTN_LEADERBOARD)
async def leaderboard_menu(message: Message):
    """Рейтинг"""
    await message.answer(f"🏆 *РЕЙТИНГ*\n\n{SECTION_UNDER_DEVELOPMENT}")

@router.message(F.text == BTN_OTHER)
async def other_menu(message: Message):
    """Ещё"""
    await message.answer(f"📋 *ЕЩЁ*\n\n{SECTION_UNDER_DEVELOPMENT}")

@router.message(F.text == BTN_SETTINGS)
async def settings_menu(message: Message):
    """Настройки"""
    await message.answer(f"⚙️ *НАСТРОЙКИ*\n\n{SECTION_UNDER_DEVELOPMENT}")

@router.message(F.text == BTN_SUPPORT)
async def support_menu(message: Message):
    """Поддержка"""
    await message.answer(f"🆘 *ПОДДЕРЖКА*\n\n{SECTION_UNDER_DEVELOPMENT}")

# === ПЕРЕХОД В ГОРОД ===

@router.message(F.text == BTN_TOWN)
async def town_menu(message: Message):
    """Переход в город"""
    try:
        from .town import show_town_menu
        await show_town_menu(message)
    except Exception as e:
        logger.error(f"❌ Ошибка города: {e}")
        await message.answer(ERROR_GENERAL)