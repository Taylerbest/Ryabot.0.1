# interfaces/telegram_bot/handlers/start.py
"""
Главный handler для /start с туториалом, статистикой и навигацией
"""

import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# Core imports
from core.use_cases.user.create_user import CreateUserUseCase, GetUserProfileUseCase, UpdateUserResourcesUseCase
from adapters.database.supabase.client import get_supabase_client
from adapters.database.supabase.repositories.user_repository import SupabaseUserRepository

# Interface imports
from ..localization.texts import get_text, t
from ..keyboards.main_menu import (
    get_start_menu, get_island_menu, get_language_keyboard,
    get_tutorial_keyboard, get_back_keyboard
)
from ..states import MenuState, TutorialState
from config.game_stats import game_stats

router = Router()
logger = logging.getLogger(__name__)


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

async def get_user_use_cases():
    """Фабрика Use Cases"""
    client = await get_supabase_client()
    user_repo = SupabaseUserRepository(client)

    return {
        'create_user': CreateUserUseCase(user_repo),
        'get_profile': GetUserProfileUseCase(user_repo),
        'update_resources': UpdateUserResourcesUseCase(user_repo)
    }


async def get_user_lang(user_id: int) -> str:
    """Получить язык пользователя без рекурсии"""
    try:
        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["language"],
            filters={"user_id": user_id},
            single=True
        )
        return user_data['language'] if user_data else 'ru'
    except:
        return 'ru'


async def format_welcome_message(stats: dict, lang: str) -> str:
    """Форматирование приветственного сообщения с статистикой"""
    uptime = stats['uptime']

    # Форматируем время работы
    if uptime['days'] > 0:
        uptime_text = t("uptime_format", lang).format(
            days=uptime['days'],
            hours=uptime['hours'],
            minutes=uptime['minutes']
        )
    else:
        uptime_text = t("uptime_format_short", lang).format(
            hours=uptime['hours'],
            minutes=uptime['minutes']
        )

    # Формируем полное сообщение
    title = t("welcome_title", lang)
    stats_text = t("welcome_stats", lang).format(
        uptime_text=uptime_text,
        total_users=stats['total_users'],
        online_users=stats['online_users'],
        new_today=stats['new_users_today'],
        new_month=stats['new_users_month'],
        qpass_holders=stats['quantum_pass_holders']
    )

    return f"{title}\n\n{stats_text}"


# === ОСНОВНЫЕ HANDLERS ===

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start с проверкой языка"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username

        logger.info(f"👤 Пользователь {user_id} (@{username}) запустил /start")

        # Получаем use cases
        use_cases = await get_user_use_cases()

        # Создаем или получаем пользователя
        user = await use_cases['create_user'].execute(user_id, username)

        # Проверяем язык
        if not user.language or user.language not in ['ru', 'en']:
            # Первый запуск - нужен выбор языка
            await message.answer(
                t("language_selection", "ru"),  # На двух языках
                reply_markup=get_language_keyboard()
            )
            await state.set_state(MenuState.LANGUAGE_SELECTION)
            return

        # Проверяем туториал
        if not user.tutorial_completed:
            # Показываем туториал
            tutorial_text = t("tutorial_shipwreck", user.language)
            await message.answer(
                tutorial_text,
                reply_markup=get_tutorial_keyboard(0, user.language)
            )
            await state.set_state(TutorialState.SHIPWRECK)
            return

        # Обычный запуск - показываем статистику
        stats = await game_stats.get_all_stats()
        welcome_text = await format_welcome_message(stats, user.language)

        await message.answer(
            welcome_text,
            reply_markup=get_start_menu(user.language)
        )
        await state.set_state(MenuState.OUTSIDE_ISLAND)

    except Exception as e:
        logger.error(f"❌ Ошибка в /start для пользователя {message.from_user.id}: {e}")
        await message.answer(t("error_init", "ru"))


# === ВЫБОР ЯЗЫКА ===

@router.callback_query(F.data.startswith("lang_"))
async def set_language_callback(callback: CallbackQuery, state: FSMContext):
    """Установка языка при первом запуске"""
    try:
        lang = callback.data.split("_")[1]
        user_id = callback.from_user.id

        logger.info(f"👤 Пользователь {user_id} выбрал язык: {lang}")

        # Сохраняем язык в БД
        client = await get_supabase_client()
        await client.execute_query(
            table="users",
            operation="update",
            data={"language": lang},
            filters={"user_id": user_id}
        )

        await callback.answer(t("language_changed", lang), show_alert=True)

        # Начинаем туториал
        tutorial_text = t("tutorial_shipwreck", lang)
        await callback.message.edit_text(
            tutorial_text,
            reply_markup=get_tutorial_keyboard(0, lang)
        )
        await state.set_state(TutorialState.SHIPWRECK)

    except Exception as e:
        logger.error(f"❌ Ошибка установки языка для {callback.from_user.id}: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


# === ТУТОРИАЛ ===

@router.callback_query(F.data == "tutorial_start")
async def tutorial_start(callback: CallbackQuery, state: FSMContext):
    """Начало туториала"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        # Переходим к пробуждению
        tutorial_text = t("tutorial_wake_up", lang)
        await callback.message.edit_text(
            tutorial_text,
            reply_markup=get_tutorial_keyboard(1, lang)
        )
        await state.set_state(TutorialState.WAKE_UP)
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка старта туториала: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


@router.callback_query(F.data.startswith("tutorial_step_"))
async def tutorial_step(callback: CallbackQuery, state: FSMContext):
    """Шаги туториала"""
    try:
        step = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        # Определяем текст и состояние
        if step == 2:
            text = t("tutorial_explore", lang)
            new_state = TutorialState.EXPLORE
        elif step == 3:
            text = t("tutorial_find_resources", lang)
            new_state = TutorialState.FIND_RESOURCES
        elif step == 4:
            text = t("tutorial_hire_worker", lang)
            new_state = TutorialState.HIRE_WORKER
            # Меняем клавиатуру для найма
            keyboard = get_tutorial_keyboard(5, lang)
        elif step == 5:
            text = t("tutorial_training", lang)
            new_state = TutorialState.TRAINING
            keyboard = get_tutorial_keyboard(6, lang)
        else:
            # Завершение
            await tutorial_complete_handler(callback, state)
            return

        # Обновляем сообщение
        if 'keyboard' not in locals():
            keyboard = get_tutorial_keyboard(step, lang)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await state.set_state(new_state)
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка шага туториала: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


@router.callback_query(F.data == "tutorial_hire_worker")
async def tutorial_hire_worker(callback: CallbackQuery, state: FSMContext):
    """Найм рабочего в туториале"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        # Списываем рябаксы и добавляем рабочего
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        if profile['ryabucks'] < 30:
            await callback.answer("💰 Недостаточно рябаксов!", show_alert=True)
            return

        # Обновляем ресурсы
        await use_cases['update_resources'].execute(user_id, {
            "ryabucks": profile['ryabucks'] - 30
        })

        # TODO: Добавить рабочего в БД (пока пропускаем)

        # Переходим к обучению
        text = t("tutorial_training", lang)
        await callback.message.edit_text(
            text,
            reply_markup=get_tutorial_keyboard(6, lang)
        )
        await state.set_state(TutorialState.TRAINING)
        await callback.answer("🎉 Джек нанят!", show_alert=True)

    except Exception as e:
        logger.error(f"❌ Ошибка найма в туториале: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


@router.callback_query(F.data.startswith("tutorial_train_"))
async def tutorial_train_specialist(callback: CallbackQuery, state: FSMContext):
    """Обучение специалиста в туториале"""
    try:
        profession = callback.data.split("_")[-1]
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        # TODO: Добавить специалиста в БД (пока пропускаем)

        profession_names = {
            "farmer": "Фермера" if lang == "ru" else "Farmer",
            "builder": "Строителя" if lang == "ru" else "Builder",
            "fisherman": "Рыбака" if lang == "ru" else "Fisherman"
        }

        profession_name = profession_names.get(profession, profession)

        await callback.answer(f"🎓 Джек обучен на {profession_name}!", show_alert=True)

        # Завершаем туториал
        await tutorial_complete_handler(callback, state)

    except Exception as e:
        logger.error(f"❌ Ошибка обучения в туториале: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


@router.callback_query(F.data == "tutorial_skip")
async def tutorial_skip(callback: CallbackQuery, state: FSMContext):
    """Пропуск туториала"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        # Отмечаем туториал как завершенный
        client = await get_supabase_client()
        await client.execute_query(
            table="users",
            operation="update",
            data={"tutorial_completed": True},
            filters={"user_id": user_id}
        )

        await callback.answer("⏭️ Туториал пропущен", show_alert=True)

        # Переходим к стартовому экрану
        stats = await game_stats.get_all_stats()
        welcome_text = await format_welcome_message(stats, lang)

        await callback.message.edit_text(welcome_text)
        await callback.message.answer(
            t("island_welcome", lang).format(
                username="Путешественник",
                level=1,
                experience=0,
                ryabucks=100,
                rbtc="0.0000",
                energy=30,
                energy_max=30
            ),
            reply_markup=get_start_menu(lang)
        )
        await state.set_state(MenuState.OUTSIDE_ISLAND)

    except Exception as e:
        logger.error(f"❌ Ошибка пропуска туториала: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


@router.callback_query(F.data == "tutorial_complete")
async def tutorial_complete_handler(callback: CallbackQuery, state: FSMContext):
    """Завершение туториала"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        # Начисляем награды
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        await use_cases['update_resources'].execute(user_id, {
            "ryabucks": profile['ryabucks'] + 200,
            "energy": min(profile['energy'] + 20, profile['energy_max'])
        })

        # Отмечаем туториал как завершенный
        client = await get_supabase_client()
        await client.execute_query(
            table="users",
            operation="update",
            data={"tutorial_completed": True, "experience": 50},
            filters={"user_id": user_id}
        )

        # Показываем сообщение о завершении
        completion_text = t("tutorial_complete", lang)
        await callback.message.edit_text(
            completion_text,
            reply_markup=get_back_keyboard("tutorial_finished", lang)
        )
        await callback.answer("🎉 Туториал завершен!", show_alert=True)

    except Exception as e:
        logger.error(f"❌ Ошибка завершения туториала: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


@router.callback_query(F.data == "tutorial_finished")
async def tutorial_finished(callback: CallbackQuery, state: FSMContext):
    """Переход к главному меню после туториала"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        # Показываем стартовый экран
        stats = await game_stats.get_all_stats()
        welcome_text = await format_welcome_message(stats, lang)

        await callback.message.edit_text(welcome_text)
        await callback.message.answer(
            "🎮 Теперь выберите действие:",
            reply_markup=get_start_menu(lang)
        )
        await state.set_state(MenuState.OUTSIDE_ISLAND)
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка перехода после туториала: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


# === ОСНОВНАЯ НАВИГАЦИЯ ===

@router.message(F.text.in_(["🏝 Войти на остров", "🏝 Enter Island"]))
async def enter_island(message: Message, state: FSMContext):
    """Вход на остров"""
    try:
        user_id = message.from_user.id
        lang = await get_user_lang(user_id)

        # Получаем профиль пользователя
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        # Формируем приветствие острова
        island_text = t("island_welcome", lang).format(
            username=profile.get('username') or "Путешественник",
            level=profile['level'],
            experience=profile['experience'],
            ryabucks=profile['ryabucks'],
            rbtc=f"{profile['rbtc']:.4f}",
            energy=profile['energy'],
            energy_max=profile['energy_max']
        )

        await message.answer(
            island_text,
            reply_markup=get_island_menu(lang)
        )
        await state.set_state(MenuState.ON_ISLAND)

    except Exception as e:
        logger.error(f"❌ Ошибка входа на остров для {message.from_user.id}: {e}")
        await message.answer(t("error_enter_island", "ru"))


@router.message(F.text.in_(["🚪 Покинуть остров", "🚪 Leave Island"]))
async def leave_island(message: Message, state: FSMContext):
    """Выход с острова"""
    try:
        user_id = message.from_user.id
        lang = await get_user_lang(user_id)

        # Показываем стартовый экран с статистикой
        stats = await game_stats.get_all_stats()
        welcome_text = await format_welcome_message(stats, lang)

        await message.answer(
            welcome_text,
            reply_markup=get_start_menu(lang)
        )
        await state.set_state(MenuState.OUTSIDE_ISLAND)

    except Exception as e:
        logger.error(f"❌ Ошибка выхода с острова: {e}")
        await message.answer(t("error_general", "ru"))


# === ЗАГЛУШКИ ДЛЯ ОСНОВНЫХ РАЗДЕЛОВ ===

@router.message(F.text.in_(["🐔 Ферма", "🐔 Farm"]))
async def farm_menu(message: Message):
    """Меню фермы (заглушка)"""
    user_id = message.from_user.id
    text = await get_text("farm_text", user_id)
    await message.answer(text)


@router.message(F.text.in_(["👤 Житель", "👤 Citizen"]))
async def citizen_menu(message: Message):
    """Меню жителя - профиль"""
    try:
        user_id = message.from_user.id
        lang = await get_user_lang(user_id)

        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        profile_text = t("profile_text", lang).format(
            username=profile.get('username') or "Путешественник",
            user_id=profile['user_id'],
            level=profile['level'],
            experience=profile['experience'],
            ryabucks=profile['ryabucks'],
            rbtc=f"{profile['rbtc']:.4f}",
            energy=profile['energy'],
            energy_max=profile['energy_max'],
            liquid_experience=profile['liquid_experience']
        )

        await message.answer(profile_text)

    except Exception as e:
        logger.error(f"❌ Ошибка показа профиля: {e}")
        await message.answer(t("error_profile", "ru"))


@router.message(F.text.in_(["💼 Работы", "💼 Work"]))
async def work_menu(message: Message):
    """Меню работ (заглушка)"""
    user_id = message.from_user.id
    text = await get_text("work_text", user_id)
    await message.answer(text)


@router.message(F.text.in_(["🎒 Инвентарь", "🎒 Inventory"]))
async def inventory_menu(message: Message):
    """Меню инвентаря (заглушка)"""
    user_id = message.from_user.id
    text = await get_text("inventory_text", user_id)
    await message.answer(text)


@router.message(F.text.in_(["👥 Друзья", "👥 Friends"]))
async def friends_menu(message: Message):
    """Меню друзей (заглушка)"""
    user_id = message.from_user.id
    text = await get_text("friends_text", user_id)
    await message.answer(text)


@router.message(F.text.in_(["🏆 Рейтинг", "🏆 Leaderboard"]))
async def leaderboard_menu(message: Message):
    """Меню рейтинга (заглушка)"""
    user_id = message.from_user.id
    text = await get_text("leaderboard_text", user_id)
    await message.answer(text)


@router.message(F.text.in_(["📋 Ещё", "📋 Other"]))
async def other_menu(message: Message):
    """Дополнительное меню (заглушка)"""
    user_id = message.from_user.id
    text = await get_text("other_text", user_id)
    await message.answer(text)


@router.message(F.text.in_(["⚙️ Настройки", "⚙️ Settings"]))
async def settings_menu(message: Message):
    """Меню настроек (заглушка)"""
    user_id = message.from_user.id
    text = await get_text("settings_text", user_id)
    await message.answer(text)


@router.message(F.text.in_(["🆘 Поддержка", "🆘 Support"]))
async def support_menu(message: Message):
    """Меню поддержки (заглушка)"""
    user_id = message.from_user.id
    text = await get_text("support_text", user_id)
    await message.answer(text)