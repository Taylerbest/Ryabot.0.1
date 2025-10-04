# interfaces/telegram_bot/handlers/start.py
"""
Handler для команды /start и главного меню с локализацией
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core.use_cases.user.create_user import CreateUserUseCase, GetUserProfileUseCase
from adapters.database.supabase.client import get_supabase_client
from adapters.database.supabase.repositories.user_repository import SupabaseUserRepository
from ..localization.texts import get_text, t
from ..keyboards.main_menu import get_start_menu, get_island_menu, get_back_to_menu_keyboard
from ..keyboards.inline_menus import get_settings_keyboard, get_language_keyboard, get_profile_keyboard, \
    get_other_menu_keyboard
from ..keyboards.town_menu import get_town_menu

router = Router()
logger = logging.getLogger(__name__)


async def get_user_use_cases():
    """Временная фабрика Use Cases"""
    client = await get_supabase_client()
    user_repo = SupabaseUserRepository(client)

    return {
        'create_user': CreateUserUseCase(user_repo),
        'get_profile': GetUserProfileUseCase(user_repo)
    }


async def get_user_lang(user_id: int) -> str:
    """Получить язык пользователя БЕЗ рекурсии"""
    try:
        from adapters.database.supabase.client import get_supabase_client

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


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or f"user{user_id}"

        logger.info(f"Пользователь {user_id} (@{username}) нажал /start")

        # Создаем или получаем пользователя
        use_cases = await get_user_use_cases()
        user = await use_cases['create_user'].execute(user_id, username)

        # Получаем язык
        lang = user.language

        # Приветственное сообщение
        welcome_text = await get_text('welcome_text', user_id, username=username)

        await message.answer(welcome_text, reply_markup=get_start_menu(lang))

    except Exception as e:
        logger.error(f"Ошибка в /start для {message.from_user.id}: {e}", exc_info=True)
        await message.answer(t('error_init'))


@router.callback_query(F.data == "enter_island")
async def enter_island(callback: CallbackQuery):
    """Вход на остров"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        # Получаем профиль
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        # Текст входа на остров
        island_text = await get_text('island_welcome_text', user_id,
                                     username=profile.get('username') or 'Житель',
                                     level=profile['level'],
                                     experience=profile['experience'],
                                     ryabucks=profile['ryabucks'],
                                     rbtc=profile['rbtc'],
                                     energy=profile['energy'],
                                     energy_max=profile['energy_max']
                                     )

        # Отправляем с постоянными кнопками
        await callback.message.answer(island_text, reply_markup=get_island_menu(lang))
        await callback.message.delete()
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка входа на остров {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer(t('error_enter_island'), show_alert=True)


# ========== ОБРАБОТЧИКИ НИЖНЕГО МЕНЮ ==========

@router.message(F.text.in_(['🐔 Ферма', '🐔 Farm']))
async def farm_menu(message: Message):
    """Меню фермы"""
    user_id = message.from_user.id
    text = await get_text('farm_text', user_id)
    await message.answer(text)


@router.message(F.text.in_(['🏘️ Город', '🏘️ Town']))
async def city_menu(message: Message):
    """Меню города"""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    text = await get_text('town_text', user_id)
    await message.answer(text, reply_markup=get_town_menu(lang))


@router.message(F.text.in_(['👤 Житель', '👤 Citizen']))
async def citizen_menu(message: Message):
    """Меню жителя"""
    try:
        user_id = message.from_user.id
        lang = await get_user_lang(user_id)
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        profile_text = await get_text('profile_text', user_id,
                                      username=profile.get('username') or 'Житель',
                                      level=profile['level'],
                                      experience=profile['experience'],
                                      ryabucks=profile['ryabucks'],
                                      rbtc=profile['rbtc'],
                                      energy=profile['energy'],
                                      energy_max=profile['energy_max'],
                                      liquid_experience=profile['liquid_experience']
                                      )

        await message.answer(profile_text, reply_markup=get_profile_keyboard(lang))

    except Exception as e:
        logger.error(f"Ошибка профиля: {e}", exc_info=True)
        await message.answer(t('error_profile'))


@router.message(F.text.in_(['💼 Рябота', '💼 Work']))
async def work_menu(message: Message):
    """Меню работ"""
    user_id = message.from_user.id
    text = await get_text('work_text', user_id)
    await message.answer(text)


@router.message(F.text.in_(['🎒 Рюкзак', '🎒 Inventory']))
async def inventory_menu(message: Message):
    """Меню рюкзака"""
    user_id = message.from_user.id
    text = await get_text('inventory_text', user_id)
    await message.answer(text)


@router.message(F.text.in_(['👥 Друзья', '👥 Friends']))
async def friends_menu(message: Message):
    """Меню друзей"""
    user_id = message.from_user.id
    text = await get_text('friends_text', user_id)
    await message.answer(text)


@router.message(F.text.in_(['🏆 Лидеры', '🏆 Leaderboard']))
async def leaderboard_menu(message: Message):
    """Меню лидеров"""
    user_id = message.from_user.id
    text = await get_text('leaderboard_text', user_id)
    await message.answer(text)


@router.message(F.text.in_(['📋 Прочее', '📋 Other']))
async def other_menu(message: Message):
    """Меню прочее"""
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    text = await get_text('other_text', user_id)
    await message.answer(text, reply_markup=get_other_menu_keyboard(lang))


# ========== ОБРАБОТЧИКИ INLINE КНОПОК ==========

@router.callback_query(F.data == "settings")
async def settings_handler(callback: CallbackQuery):
    """Настройки"""
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    text = await get_text('settings_text', user_id)
    await callback.message.edit_text(text, reply_markup=get_settings_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "language")
@router.callback_query(F.data == "change_language")
async def language_handler(callback: CallbackQuery):
    """Выбор языка"""
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    text = await get_text('language_text', user_id)
    await callback.message.edit_text(text, reply_markup=get_language_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    """Установка языка"""
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # TODO: Сохранить язык в БД

    await callback.answer(t('language_changed', lang), show_alert=True)
    await callback.message.edit_text(
        t('language_changed_success', lang),
        reply_markup=get_settings_keyboard(lang)
    )


@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery):
    """Профиль"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        profile_text = await get_text('profile_text', user_id,
                                      username=profile.get('username') or 'Житель',
                                      level=profile['level'],
                                      experience=profile['experience'],
                                      ryabucks=profile['ryabucks'],
                                      rbtc=profile['rbtc'],
                                      energy=profile['energy'],
                                      energy_max=profile['energy_max'],
                                      liquid_experience=profile['liquid_experience']
                                      )

        await callback.message.edit_text(profile_text, reply_markup=get_profile_keyboard(lang))
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка профиля: {e}", exc_info=True)
        await callback.answer(t('error_profile'), show_alert=True)


@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    """Возврат в стартовое меню"""
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    text = await get_text('welcome_title', user_id)
    await callback.message.edit_text(text, reply_markup=get_start_menu(lang))
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат - просто удаляем сообщение"""
    await callback.message.delete()
    await callback.answer()


# ========== ОБРАБОТЧИКИ ЗДАНИЙ ГОРОДА ==========

@router.callback_query(F.data.in_(['townhall', 'market', 'academy', 'ryabank', 'products',
                                   'pawnshop', 'tavern1', 'entertainment', 'realestate',
                                   'vetclinic', 'construction', 'hospital', 'quantumhub', 'cemetery']))
async def building_handler(callback: CallbackQuery):
    """Обработчик всех зданий города"""
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    building = callback.data

    text = await get_text(f'{building}_text', user_id)
    await callback.message.edit_text(text, reply_markup=get_town_menu(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    """Установка языка"""
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Сохраняем язык в БД
    try:
        use_cases = await get_user_use_cases()
        user_repo = use_cases['get_profile'].user_repo  # Получаем репозиторий

        # Обновляем язык пользователя
        await user_repo.update_resources(user_id, {"language": lang})

        await callback.answer(t('language_changed', lang), show_alert=True)
        await callback.message.edit_text(
            t('language_changed_success', lang),
            reply_markup=get_settings_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Ошибка смены языка: {e}")
        await callback.answer("Ошибка смены языка", show_alert=True)
