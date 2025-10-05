# interfaces/telegram_bot/handlers/tutorial.py
"""
Полный туториал с созданием персонажа по новому плану
"""

import logging
import asyncio
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

# Core imports
from core.use_cases.user.create_user import CreateUserUseCase, GetUserProfileUseCase, UpdateUserResourcesUseCase
from adapters.database.supabase.client import get_supabase_client
from adapters.database.supabase.repositories.user_repository import SupabaseUserRepository
from core.domain.entities import TutorialStep, CharacterPreset

# Config
from config.texts import *
from config.game_stats import game_stats

# Services
from services.blockchain_service import blockchain_service
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

def get_character_keyboard():
    """Клавиатура выбора персонажа"""
    keyboard = []
    for i in range(1, 11, 2):  # 5 строк по 2 персонажа
        row = [
            InlineKeyboardButton(
                text=f"{i}. {CHARACTER_NAMES[i][:15]}...",
                callback_data=f"char_{i}"
            )
        ]
        if i + 1 <= 10:
            row.append(
                InlineKeyboardButton(
                    text=f"{i+1}. {CHARACTER_NAMES[i+1][:15]}...",
                    callback_data=f"char_{i+1}"
                )
            )
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_tutorial_keyboard(step: str):
    """Клавиатура для туториала"""
    if step == "character_selected":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BTN_TUTORIAL_START, callback_data="tutorial_shipwreck")]
        ])
    elif step == "shipwreck":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BTN_CONTINUE, callback_data="tutorial_tavern")]
        ])
    elif step == "tavern":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💍 Пойти в ломбард", callback_data="tutorial_pawnshop")]
        ])
    elif step == "pawnshop":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Продать за 500 💵", callback_data="tutorial_sell_shard")]
        ])
    elif step == "pawnshop_sold":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏛️ Идти в ратушу", callback_data="tutorial_townhall")]
        ])
    elif step == "townhall_register":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Зарегистрироваться за 10 💵", callback_data="tutorial_register")]
        ])
    elif step == "townhall_registered":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📜 Купить лицензию работодателя", callback_data="tutorial_employer_license")]
        ])
    elif step == "employer_license":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Купить за 100 💵", callback_data="tutorial_buy_employer_license")]
        ])
    elif step == "license_bought":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎓 Идти в академию", callback_data="tutorial_academy")]
        ])
    elif step == "academy_hire":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👷 Нанять рабочего за 30 💵", callback_data="tutorial_hire_worker")]
        ])
    elif step == "worker_hired":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💼 Отправить на работу", callback_data="tutorial_first_work")]
        ])
    elif step == "first_work":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌊 Начать работу", callback_data="tutorial_do_work")]
        ])
    elif step == "work_completed":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Получить опыт у жителя", callback_data="tutorial_citizen")]
        ])
    elif step == "citizen_quest":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎓 Обучить специалиста", callback_data="tutorial_train")]
        ])
    elif step == "train_specialist":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👨‍🌾 Обучить фермера", callback_data="tutorial_train_farmer")],
            [InlineKeyboardButton(text="🏗️ Обучить строителя", callback_data="tutorial_train_builder")]
        ])
    elif step == "specialist_trained":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏛️ Купить фермерскую лицензию", callback_data="tutorial_farm_license")]
        ])
    # Можно продолжить для остальных шагов...
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BTN_CONTINUE, callback_data="tutorial_continue")]
        ])

# === СОЗДАНИЕ ПЕРСОНАЖА ===

@router.callback_query(F.data == "start_character_creation")
async def start_character_creation(callback: CallbackQuery, state: FSMContext):
    """Начало создания персонажа"""
    try:
        await callback.message.edit_text(
            CHARACTER_CREATION_TITLE,
            reply_markup=get_character_keyboard()
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка создания персонажа: {e}")
        await callback.answer("Ошибка создания персонажа", show_alert=True)

@router.callback_query(F.data.startswith("char_"))
async def select_character(callback: CallbackQuery, state: FSMContext):
    """Выбор персонажа"""
    try:
        char_id = int(callback.data.split("_")[1])
        user_id = callback.from_user.id

        # Обновляем персонажа в БД
        client = await get_supabase_client()
        await client.execute_query(
            table="users",
            operation="update",
            data={
                "character_preset": char_id,
                "tutorial_step": TutorialStep.SHIPWRECK.value
            },
            filters={"user_id": user_id}
        )

        # Показываем выбранного персонажа
        text = CHARACTER_SELECTED.format(
            name=CHARACTER_NAMES[char_id],
            description=CHARACTER_DESCRIPTIONS[char_id]
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_tutorial_keyboard("character_selected")
        )
        await callback.answer(f"Персонаж {CHARACTER_NAMES[char_id]} выбран!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка выбора персонажа: {e}")
        await callback.answer("Ошибка выбора персонажа", show_alert=True)

# === ТУТОРИАЛ ===

@router.callback_query(F.data == "tutorial_shipwreck")
async def tutorial_shipwreck(callback: CallbackQuery):
    """Кораблекрушение"""
    try:
        await callback.message.edit_text(
            TUTORIAL_SHIPWRECK,
            reply_markup=get_tutorial_keyboard("shipwreck")
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка туториала кораблекрушения: {e}")
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "tutorial_tavern")
async def tutorial_tavern(callback: CallbackQuery):
    """Посещение таверны"""
    try:
        user_id = callback.from_user.id

        # Обновляем шаг туториала
        await tutorial_service.update_tutorial_step(user_id, TutorialStep.TAVERN_VISIT)

        await callback.message.edit_text(
            TUTORIAL_TAVERN,
            reply_markup=get_tutorial_keyboard("tavern")
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка туториала таверны: {e}")
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "tutorial_pawnshop")
async def tutorial_pawnshop(callback: CallbackQuery):
    """Посещение ломбарда"""
    try:
        user_id = callback.from_user.id

        await tutorial_service.update_tutorial_step(user_id, TutorialStep.PAWN_SHOP)

        await callback.message.edit_text(
            TUTORIAL_PAWNSHOP,
            reply_markup=get_tutorial_keyboard("pawnshop")
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка туториала ломбарда: {e}")
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "tutorial_sell_shard")
async def tutorial_sell_shard(callback: CallbackQuery):
    """Продажа золотого осколка"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        # Обновляем ресурсы: убираем осколок, добавляем рябаксы
        use_cases = await get_user_use_cases()
        await use_cases['update_resources'].execute(user_id, {
            "ryabucks": 500,
            "golden_shards": 0
        })

        # Логируем в блокчейн
        await blockchain_service.log_action(
            "SHARD_SOLD", user_id, username,
            {"shard_type": "golden", "price": 500, "currency": "ryabucks"},
            significance=1  # Важное событие
        )

        await tutorial_service.update_tutorial_step(user_id, TutorialStep.TOWN_HALL_REGISTER)

        await callback.message.edit_text(
            TUTORIAL_PAWNSHOP_SOLD,
            reply_markup=get_tutorial_keyboard("pawnshop_sold")
        )
        await callback.answer("💰 Осколок продан за 500 рябаксов!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка продажи осколка: {e}")
        await callback.answer("Ошибка продажи", show_alert=True)

@router.callback_query(F.data == "tutorial_townhall")
async def tutorial_townhall(callback: CallbackQuery):
    """Ратуша - регистрация"""
    try:
        user_id = callback.from_user.id

        await callback.message.edit_text(
            TUTORIAL_TOWNHALL_REGISTER,
            reply_markup=get_tutorial_keyboard("townhall_register")
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка ратуши: {e}")
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "tutorial_register")
async def tutorial_register(callback: CallbackQuery):
    """Регистрация гражданина"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        # Списываем деньги
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        if profile['ryabucks'] < 10:
            await callback.answer("Недостаточно рябаксов!", show_alert=True)
            return

        await use_cases['update_resources'].execute(user_id, {
            "ryabucks": profile['ryabucks'] - 10
        })

        # Логируем регистрацию в блокчейн
        await blockchain_service.log_action(
            "CITIZEN_REGISTERED", user_id, username,
            {"fee_paid": 10, "status": "citizen"},
            significance=2  # Эпическое событие - новый гражданин!
        )

        await tutorial_service.update_tutorial_step(user_id, TutorialStep.EMPLOYER_LICENSE)

        text = TUTORIAL_TOWNHALL_REGISTERED.format(username=username)
        await callback.message.edit_text(
            text,
            reply_markup=get_tutorial_keyboard("townhall_registered")
        )
        await callback.answer("🎉 Вы гражданин острова!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка регистрации: {e}")
        await callback.answer("Ошибка регистрации", show_alert=True)

@router.callback_query(F.data == "tutorial_employer_license")
async def tutorial_employer_license(callback: CallbackQuery):
    """Покупка лицензии работодателя"""
    try:
        await callback.message.edit_text(
            TUTORIAL_EMPLOYER_LICENSE,
            reply_markup=get_tutorial_keyboard("employer_license")
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка лицензии: {e}")
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "tutorial_buy_employer_license")
async def tutorial_buy_employer_license(callback: CallbackQuery):
    """Покупка лицензии работодателя"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        # Списываем деньги и выдаем лицензию
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        if profile['ryabucks'] < 100:
            await callback.answer("Недостаточно рябаксов!", show_alert=True)
            return

        await use_cases['update_resources'].execute(user_id, {
            "ryabucks": profile['ryabucks'] - 100
        })

        # Обновляем лицензию в БД
        client = await get_supabase_client()
        await client.execute_query(
            table="users",
            operation="update",
            data={"has_employer_license": True},
            filters={"user_id": user_id}
        )

        # Логируем покупку лицензии
        await blockchain_service.log_action(
            "LICENSE_PURCHASED", user_id, username,
            {"license_type": "employer", "level": 1, "price": 100},
            significance=1
        )

        await tutorial_service.update_tutorial_step(user_id, TutorialStep.ACADEMY_HIRE)

        remaining = profile['ryabucks'] - 100
        text = TUTORIAL_LICENSE_BOUGHT.format(remaining=remaining)

        await callback.message.edit_text(
            text,
            reply_markup=get_tutorial_keyboard("license_bought")
        )
        await callback.answer("📜 Лицензия получена!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка покупки лицензии: {e}")
        await callback.answer("Ошибка покупки", show_alert=True)

@router.callback_query(F.data == "tutorial_academy")
async def tutorial_academy(callback: CallbackQuery):
    """Академия - найм рабочего"""
    try:
        user_id = callback.from_user.id

        # Получаем текущие рябаксы
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        text = TUTORIAL_ACADEMY_HIRE.format(ryabucks=profile['ryabucks'])

        await callback.message.edit_text(
            text,
            reply_markup=get_tutorial_keyboard("academy_hire")
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка академии: {e}")
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "tutorial_hire_worker")
async def tutorial_hire_worker(callback: CallbackQuery):
    """Найм первого рабочего"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        # Списываем деньги
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        if profile['ryabucks'] < 30:
            await callback.answer("Недостаточно рябаксов!", show_alert=True)
            return

        await use_cases['update_resources'].execute(user_id, {
            "ryabucks": profile['ryabucks'] - 30
        })

        # Добавляем рабочего в БД
        client = await get_supabase_client()
        await client.execute_query(
            table="specialists",
            operation="insert",
            data={
                "user_id": user_id,
                "specialist_type": "worker",
                "level": 1,
                "experience": 0,
                "hired_at": datetime.now().isoformat()
            }
        )

        # Логируем найм
        await blockchain_service.log_action(
            "WORKER_HIRED", user_id, username,
            {"worker_type": "laborer", "cost": 30, "name": "Иван"},
            significance=1
        )

        await tutorial_service.update_tutorial_step(user_id, TutorialStep.WORK_TASK)

        await callback.message.edit_text(
            TUTORIAL_WORKER_HIRED,
            reply_markup=get_tutorial_keyboard("worker_hired")
        )
        await callback.answer("👷 Рабочий Иван нанят!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка найма рабочего: {e}")
        await callback.answer("Ошибка найма", show_alert=True)

@router.callback_query(F.data == "tutorial_first_work")
async def tutorial_first_work(callback: CallbackQuery):
    """Первая работа"""
    try:
        await callback.message.edit_text(
            TUTORIAL_FIRST_WORK,
            reply_markup=get_tutorial_keyboard("first_work")
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка первой работы: {e}")
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "tutorial_do_work")
async def tutorial_do_work(callback: CallbackQuery):
    """Выполнение первой работы"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        # Проверяем энергию
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        if profile['energy'] < 5:
            await callback.answer("Недостаточно энергии! Нужно 5.", show_alert=True)
            return

        # Награды за работу
        await use_cases['update_resources'].execute(user_id, {
            "ryabucks": profile['ryabucks'] + 50,
            "energy": profile['energy'] - 5,
            "experience": profile['experience'] + 25
        })

        # Логируем выполнение работы
        await blockchain_service.log_action(
            "WORK_COMPLETED", user_id, username,
            {"task": "sea_unload", "reward_money": 50, "reward_exp": 25},
            significance=0
        )

        await tutorial_service.update_tutorial_step(user_id, TutorialStep.CITIZEN_QUEST)

        await callback.message.edit_text(
            TUTORIAL_WORK_COMPLETED,
            reply_markup=get_tutorial_keyboard("work_completed")
        )
        await callback.answer("✅ Работа выполнена!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка выполнения работы: {e}")
        await callback.answer("Ошибка работы", show_alert=True)

@router.callback_query(F.data == "tutorial_citizen")
async def tutorial_citizen(callback: CallbackQuery):
    """Задание жителя"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        # Даем дополнительный опыт и жидкий опыт
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        await use_cases['update_resources'].execute(user_id, {
            "experience": profile['experience'] + 50,
            "liquid_experience": profile['liquid_experience'] + 10
        })

        await tutorial_service.update_tutorial_step(user_id, TutorialStep.TRAIN_SPECIALIST)

        await callback.message.edit_text(
            TUTORIAL_CITIZEN_QUEST,
            reply_markup=get_tutorial_keyboard("citizen_quest")
        )
        await callback.answer("📊 Опыт получен!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка задания жителя: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "tutorial_train")
async def tutorial_train_menu(callback: CallbackQuery):
    """Меню выбора специалиста для обучения"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        # Показываем меню обучения
        await callback.message.edit_text(
            TUTORIAL_TRAIN_SPECIALIST,
            reply_markup=get_tutorial_keyboard("train_specialist")
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка меню обучения: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "tutorial_train_farmer")
async def tutorial_train_farmer(callback: CallbackQuery):
    """Обучение фермера"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        # Списываем ресурсы
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        if profile['liquid_experience'] < 25 or profile['ryabucks'] < 50:
            await callback.answer("Недостаточно ресурсов!", show_alert=True)
            return

        await use_cases['update_resources'].execute(user_id, {
            "liquid_experience": profile['liquid_experience'] - 25,
            "ryabucks": profile['ryabucks'] - 50
        })

        # Обновляем специалиста в БД
        client = await get_supabase_client()
        await client.execute_query(
            table="specialists",
            operation="update",
            data={"specialist_type": "farmer"},
            filters={"user_id": user_id, "specialist_type": "worker"}
        )

        # Логируем
        await blockchain_service.log_action(
            "SPECIALIST_TRAINED", user_id, username,
            {"specialty": "farmer", "cost_exp": 25, "cost_money": 50},
            significance=1
        )

        await tutorial_service.update_tutorial_step(user_id, TutorialStep.FARM_LICENSE)

        # Показываем результат
        text = TUTORIAL_SPECIALIST_TRAINED.format(
            specialty=SPECIALTY_FARMER,
            specialty_abilities=SPECIALTY_ABILITIES["farmer"]
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_tutorial_keyboard("specialist_trained")
        )
        await callback.answer("🎓 Фермер обучен!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка обучения фермера: {e}")
        await callback.answer("Ошибка обучения", show_alert=True)


@router.callback_query(F.data == "tutorial_train_builder")
async def tutorial_train_builder(callback: CallbackQuery):
    """Обучение строителя"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        # Аналогично фермеру, но с типом builder
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        if profile['liquid_experience'] < 25 or profile['ryabucks'] < 50:
            await callback.answer("Недостаточно ресурсов!", show_alert=True)
            return

        await use_cases['update_resources'].execute(user_id, {
            "liquid_experience": profile['liquid_experience'] - 25,
            "ryabucks": profile['ryabucks'] - 50
        })

        # Обновляем специалиста
        client = await get_supabase_client()
        await client.execute_query(
            table="specialists",
            operation="update",
            data={"specialist_type": "builder"},
            filters={"user_id": user_id, "specialist_type": "worker"}
        )

        # Логируем
        await blockchain_service.log_action(
            "SPECIALIST_TRAINED", user_id, username,
            {"specialty": "builder", "cost_exp": 25, "cost_money": 50},
            significance=1
        )

        await tutorial_service.update_tutorial_step(user_id, TutorialStep.FARM_LICENSE)

        # Показываем результат
        text = TUTORIAL_SPECIALIST_TRAINED.format(
            specialty=SPECIALTY_BUILDER,
            specialty_abilities=SPECIALTY_ABILITIES["builder"]
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_tutorial_keyboard("specialist_trained")
        )
        await callback.answer("🎓 Строитель обучен!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка обучения строителя: {e}")
        await callback.answer("Ошибка обучения", show_alert=True)

# === ПРОДОЛЖЕНИЕ ТУТОРИАЛА ===

# Можно добавить остальные шаги туториала аналогично...
# Это базовая структура, которую можно расширить

@router.callback_query(F.data == "tutorial_continue")
async def tutorial_continue(callback: CallbackQuery):
    """Продолжение туториала (заглушка)"""
    try:
        await callback.answer("🚧 Продолжение туториала в разработке!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка продолжения туториала: {e}")
        await callback.answer("Ошибка", show_alert=True)