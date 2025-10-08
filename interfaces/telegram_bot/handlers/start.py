# interfaces/telegram_bot/handlers/start.py
"""
Главный handler с новой структурой меню + сохранением туториала
"""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config.texts import (
    LANGUAGE_SELECTION_TITLE,
    ERROR_GENERAL,
    BTN_SETTINGS
)
from config.settings import settings
from core.domain.entities import TutorialStep
from adapters.database.supabase.client import get_supabase_client
from interfaces.telegram_bot.keyboards.mainmenu import get_start_menu
from interfaces.telegram_bot.keyboards.inlinemenus import (
    get_language_keyboard,
    get_settings_keyboard  # ← Добавьте этот импорт
)
from services.tutorialservice import tutorial_service
from utils.base62_helper import decode_player_id

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
        is_persistent=True,
        input_field_placeholder="Выберите раздел острова"
    )


# ОБРАБОТЧИК: кнопка "Настройки"
@router.message(F.text == BTN_SETTINGS)
async def settings_menu_message(message: Message):
    """Открытие меню настроек"""
    try:
        user_id = message.from_user.id

        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["display_name", "username", "language", "character_preset"],
            filters={"user_id": user_id},
            single=True
        )

        if not user_data:
            await message.answer("❌ Пользователь не найден. Используйте /start")
            return

        display_name = user_data.get("display_name") or user_data.get("username", "Не установлено")
        language = user_data.get("language", "ru")
        character = user_data.get("character_preset", 1)

        settings_text = (
            f"⚙️ **Настройки**\n\n"
            f"📝 Отображаемое имя: `{display_name}`\n"
            f"🌍 Язык: `{'Русский' if language == 'ru' else 'English'}`\n"
            f"👤 Персонаж: `#{character}`\n\n"
            f"Выберите, что хотите изменить:"
        )

        await message.answer(settings_text, reply_markup=get_settings_keyboard())

    except Exception as e:
        logger.error(f"Error showing settings: {e}")
        await message.answer("❌ Произошла ошибка при загрузке настроек")


# ОБРАБОТЧИК: начало смены имени из настроек
@router.callback_query(F.data == "settings_change_name")
async def change_name_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса смены имени"""
    try:
        user_id = callback.from_user.id

        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["display_name", "username"],
            filters={"user_id": user_id},
            single=True
        )

        current_name = user_data.get("display_name") or user_data.get("username", "Не установлено")

        text = (
            f"📝 **Изменение отображаемого имени**\n\n"
            f"Текущее имя: `{current_name}`\n\n"
            f"Введите новое отображаемое имя (3-20 символов):\n\n"
            f"💡 Это имя будут видеть другие игроки в рейтингах, на карте и в списке друзей."
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="settings_cancel")]
        ])

        await callback.message.edit_text(text, reply_markup=keyboard)
        await state.set_state(TutorialState.WAITING_FOR_DISPLAY_NAME)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error starting name change: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


# ОБРАБОТЧИК: обработка нового имени
@router.message(TutorialState.WAITING_FOR_DISPLAY_NAME)
async def change_name_process(message: Message, state: FSMContext):
    """Обработка нового имени"""
    try:
        user_id = message.from_user.id
        new_name = message.text.strip()

        # Импортируем use case
        from core.use_cases.user.update_display_name import UpdateDisplayNameUseCase
        from adapters.database.supabase.repositories.user_repository import SupabaseUserRepository

        # Создаём use case
        client = await get_supabase_client()
        user_repo = SupabaseUserRepository(client)
        use_case = UpdateDisplayNameUseCase(user_repo)

        # Выполняем обновление
        success, msg = await use_case.execute(user_id, new_name)

        if success:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⚙️ Настройки", callback_data="back_to_settings")],
                [InlineKeyboardButton(text="◀️ Главное меню", callback_data="settings_back")]
            ])
            await message.answer(f"✅ {msg}", reply_markup=keyboard)
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="settings_change_name")],
                [InlineKeyboardButton(text="⚙️ Настройки", callback_data="back_to_settings")]
            ])
            await message.answer(f"❌ {msg}", reply_markup=keyboard)

        await state.clear()

    except Exception as e:
        logger.error(f"Error changing display name: {e}")
        await message.answer("❌ Произошла ошибка при изменении имени")
        await state.clear()


# ОБРАБОТЧИК: возврат в настройки
@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    """Возврат в меню настроек"""
    try:
        user_id = callback.from_user.id

        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["display_name", "username", "language", "character_preset"],
            filters={"user_id": user_id},
            single=True
        )

        display_name = user_data.get("display_name") or user_data.get("username", "Не установлено")
        language = user_data.get("language", "ru")
        character = user_data.get("character_preset", 1)

        settings_text = (
            f"⚙️ **Настройки**\n\n"
            f"📝 Отображаемое имя: `{display_name}`\n"
            f"🌍 Язык: `{'Русский' if language == 'ru' else 'English'}`\n"
            f"👤 Персонаж: `#{character}`\n\n"
            f"Выберите, что хотите изменить:"
        )

        await callback.message.edit_text(settings_text, reply_markup=get_settings_keyboard())
        await callback.answer()

    except Exception as e:
        logger.error(f"Error returning to settings: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


# ОБРАБОТЧИК: отмена
@router.callback_query(F.data == "settings_cancel")
async def settings_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена текущего действия в настройках"""
    await state.clear()
    await back_to_settings(callback)


@router.callback_query(F.data == "settings_back")
async def settings_back_to_menu(callback: CallbackQuery):
    """Закрытие настроек"""
    await callback.message.delete()
    await callback.answer("Настройки закрыты")

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


async def get_total_burned_rbtc(client) -> float:
    """Получить общее количество сожженных RBTC"""
    try:
        # ✅ ИСПРАВЛЕНО: используем pool_transactions вместо bank_transactions
        burned_transactions = await client.execute_query(
            table="bank_transactions",
            operation="select",
            columns=["amount_from"],
            filters={"currency_to": "burned"}
        )

        if not burned_transactions:
            return 0.0

        # Суммировать все сожженные RBTC
        total_burned = sum(float(tx.get('amount_from', 0)) for tx in burned_transactions)
        return total_burned

    except Exception as e:
        logger.error(f"Ошибка получения сожженных RBTC: {e}")
        return 0.0


async def get_island_stats() -> dict:
    """Получить статистику острова"""
    try:
        client = await get_supabase_client()

        # Вызвать функцию для получения сожженных RBTC
        total_burned_rbtc = await get_total_burned_rbtc(client)

        # Рассчитать процент
        burn_percentage = (total_burned_rbtc / 17_850_000) * 100 if total_burned_rbtc > 0 else 0.0

        return {
            'total_rbtc_mined': 0,
            'total_burned_rbtc': total_burned_rbtc,
            'burn_percentage': burn_percentage,
            'quantum_labs': 0,
            'friends_total': 0,
            'expeditions_total': 0,
            'anomalies_total': 0,
            'fights_total': 0,
            'races_total': 0,
            'boxes_total': 0
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики острова: {e}")
        return {
            'total_rbtc_mined': 0,
            'total_burned_rbtc': 0,
            'burn_percentage': 0,
            'quantum_labs': 0,
            'friends_total': 0,
            'expeditions_total': 0,
            'anomalies_total': 0,
            'fights_total': 0,
            'races_total': 0,
            'boxes_total': 0
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
            columns=["user_id", "tutorial_step", "has_island_access", "has_employer_license", "referred_by"],
            filters={"user_id": user_id},
            single=True
        )

        is_new_user = user_data is None

        # Обработка реферального кода (ТОЛЬКО для новых пользователей)
        referrer_user_id = None
        args = message.text.split()

        if is_new_user and len(args) > 1 and args[1].startswith("ref"):
            ref_code = args[1][3:]  # Убираем префикс "ref"
            referrer_player_id = decode_player_id(ref_code)

            if referrer_player_id > 0:
                logger.info(f"Пользователь {user_id} перешел по реф-ссылке от player_id {referrer_player_id}")

                # Получаем user_id реферера по player_id
                referrer_data = await client.execute_query(
                    table="users",
                    operation="select",
                    columns=["user_id"],
                    filters={"player_id": referrer_player_id},
                    single=True
                )

                if referrer_data:
                    referrer_user_id = referrer_data["user_id"]
                    logger.info(f"Найден реферер: user_id {referrer_user_id}")
                else:
                    logger.warning(f"Реферер с player_id {referrer_player_id} не найден")

        # Если пользователя нет - создаем
        if is_new_user:
            insert_data = {
                "user_id": user_id,
                "username": username,
                "ryabucks": 100,
                "golden_shards": 1,
                "tutorial_step": "not_started"
            }

            # Добавляем реферера, если есть
            if referrer_user_id:
                insert_data["referred_by"] = referrer_user_id

            await client.execute_query(
                table="users",
                operation="insert",
                data=insert_data
            )

            # Если был реферер - создаем реферальную запись
            if referrer_user_id:
                try:
                    await client.execute_query(
                        table="referrals",
                        operation="insert",
                        data={
                            "referrer_user_id": referrer_user_id,
                            "referred_user_id": user_id,
                            "referral_type": "friend",
                            "created_at": datetime.now().isoformat(),
                            "is_active": True
                        }
                    )
                    logger.info(f"✅ Реферальная связь создана: {referrer_user_id} -> {user_id}")

                    # Опционально: уведомить реферера
                    try:
                        from aiogram import Bot
                        from config.settings import settings
                        bot = Bot(token=settings.BOT_TOKEN)
                        await bot.send_message(
                            referrer_user_id,
                            f"🎉 По вашей реферальной ссылке зарегистрировался новый игрок!\n"
                            f"Следите за его прогрессом в разделе «Друзья»"
                        )
                    except Exception as notify_error:
                        logger.warning(f"Не удалось уведомить реферера: {notify_error}")

                except Exception as ref_error:
                    logger.error(f"Ошибка создания реферальной записи: {ref_error}")

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

        await message.answer(
            "🏝",  # Минимальный текст
            reply_markup=get_island_menu()
        )

        stats = await get_island_stats()
        menu_text = ISLAND_MAIN_MENU.format(**stats)



        # Отправляем инлайн меню со статистикой
        await message.answer(
            menu_text,
            reply_markup=get_stats_keyboard("rbtc")
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
async def settings_menu_message(message: Message):
    """Обработчик кнопки 'Настройки'"""
    try:
        user_id = message.from_user.id
        client = await get_supabase_client()

        # Получаем данные пользователя с обработкой отсутствующих полей
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["display_name", "username", "language", "character_preset", "tutorial_completed"],
            filters={"user_id": user_id},
            single=True
        )

        if not user_data:
            await message.answer("❌ Пользователь не найден. Используйте /start")
            return

        # Безопасное получение данных с fallback значениями
        display_name = user_data.get("display_name") or user_data.get("username") or f"Игрок {user_id}"
        language = user_data.get("language", "ru")
        character = user_data.get("character_preset", 1)
        tutorial_completed = user_data.get("tutorial_completed", False)

        # Проверка завершения туториала
        if not tutorial_completed:
            await message.answer(
                "⚠️ Настройки станут доступны после завершения туториала.\n"
                "Продолжите знакомство с островом!"
            )
            return

        settings_text = (
            f"⚙️ Настройки\n\n"
            f"👤 Имя: {display_name}\n"
            f"🌐 Язык: {'Русский' if language == 'ru' else 'English'}\n"
            f"🎭 Персонаж: {character}\n"
        )

        await message.answer(settings_text, reply_markup=get_settings_keyboard())

    except Exception as e:
        logger.error(f"Error showing settings for user {message.from_user.id}: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при загрузке настроек.\n"
            "Попробуйте позже или используйте /start"
        )


@router.message(F.text == BTN_SUPPORT)
async def support_menu(message: Message):
    """Поддержка"""
    await message.answer(f"🆘 *ПОДДЕРЖКА*\n\n{SECTION_UNDER_DEVELOPMENT}")
