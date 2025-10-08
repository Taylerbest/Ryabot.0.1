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
from interfaces.telegram_bot.states import TutorialState

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
                "character_preset": char_id
            },
            filters={"user_id": user_id}
        )

        # ИЗМЕНЕНО: Запрашиваем имя ВМЕСТО показа выбранного персонажа
        text = (
            f"✅ **Персонаж выбран!**\n\n"
            f"👤 {CHARACTER_NAMES[char_id]}\n"
            f"_{CHARACTER_DESCRIPTIONS[char_id]}_\n\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📝 **Как вас будут называть на острове?**\n\n"
            f"Введите своё игровое имя (3-20 символов):\n\n"
            f"💡 Это имя будут видеть другие игроки в рейтингах, на карте и в списке друзей."
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_display_name")]
        ])

        await callback.message.edit_text(text, reply_markup=keyboard)

        # Импортируем состояние
        from interfaces.telegram_bot.states import TutorialState
        await state.set_state(TutorialState.WAITING_FOR_DISPLAY_NAME)
        await callback.answer(f"Персонаж {CHARACTER_NAMES[char_id]} выбран!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка выбора персонажа: {e}")
        await callback.answer("Ошибка выбора персонажа", show_alert=True)


# === ОБРАБОТКА ВВОДА ИМЕНИ ПОСЛЕ ВЫБОРА ПЕРСОНАЖА ===

@router.message(TutorialState.WAITING_FOR_DISPLAY_NAME)
async def process_display_name_in_tutorial(message: Message, state: FSMContext):
    """Обработка ввода имени в туториале"""
    try:
        user_id = message.from_user.id
        new_name = message.text.strip()

        logger.info(f"Пользователь {user_id} вводит имя: {new_name}")

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
            # Имя установлено успешно - продолжаем туториал
            await state.clear()

            # Обновляем шаг туториала
            await client.execute_query(
                table="users",
                operation="update",
                data={"tutorial_step": TutorialStep.SHIPWRECK.value},
                filters={"user_id": user_id}
            )

            welcome_text = (
                f"✅ **Отлично, {new_name}!**\n\n"
                f"Теперь начнём ваше приключение на острове...\n\n"
                f"🌊 Вы просыпаетесь на берегу после кораблекрушения..."
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_TUTORIAL_START, callback_data="tutorial_shipwreck")]
            ])

            await message.answer(welcome_text, reply_markup=keyboard)
        else:
            # Ошибка валидации или имя занято
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать другое имя", callback_data="retry_display_name")],
                [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_display_name")]
            ])
            await message.answer(f"❌ {msg}\n\nПопробуйте другое имя:", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка обработки имени в туториале: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка. Попробуйте ещё раз или пропустите этот шаг.")
        await state.clear()


@router.callback_query(F.data == "retry_display_name")
async def retry_display_name(callback: CallbackQuery, state: FSMContext):
    """Повтор ввода имени"""
    text = (
        f"📝 **Введите другое имя**\n\n"
        f"Требования:\n"
        f"• От 3 до 20 символов\n"
        f"• Имя должно быть уникальным\n\n"
        f"Введите новое имя:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_display_name")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)

    from interfaces.telegram_bot.states import TutorialState
    await state.set_state(TutorialState.WAITING_FOR_DISPLAY_NAME)
    await callback.answer()


@router.callback_query(F.data == "skip_display_name")
async def skip_display_name(callback: CallbackQuery, state: FSMContext):
    """Пропуск ввода имени"""
    try:
        user_id = callback.from_user.id
        await state.clear()

        # Обновляем шаг туториала
        client = await get_supabase_client()
        await client.execute_query(
            table="users",
            operation="update",
            data={"tutorial_step": TutorialStep.SHIPWRECK.value},
            filters={"user_id": user_id}
        )

        text = (
            f"⏭️ **Имя не установлено**\n\n"
            f"Вы сможете изменить его позже в настройках.\n\n"
            f"🌊 Начинаем ваше приключение...\n\n"
            f"Вы просыпаетесь на берегу после кораблекрушения..."
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BTN_TUTORIAL_START, callback_data="tutorial_shipwreck")]
        ])

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer("Имя можно будет изменить в настройках")

    except Exception as e:
        logger.error(f"Ошибка пропуска имени: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.message(TutorialStates.waiting_for_display_name)
async def process_display_name_in_tutorial(message: Message, state: FSMContext):
    """Обработка ввода игрового имени"""
    user_id = message.from_user.id
    display_name = message.text.strip()

    logger.info(f"Пользователь {user_id} ввел имя: {display_name}")

    try:
        # Валидация длины
        if len(display_name) < 3 or len(display_name) > 12:
            await message.answer(
                "❌ Имя должно быть от 3 до 12 символов. Попробуй еще раз:",
                reply_markup=None
            )
            return

        # Валидация символов
        if not re.match(r'^[a-zA-Zа-яА-Я0-9_-]+$', display_name):
            await message.answer(
                "❌ Используй только буквы, цифры, _ и -\nПопробуй еще раз:",
                reply_markup=None
            )
            return

        # Проверка уникальности
        client = await get_supabase_client()
        user_repo = SupabaseUserRepository(client)

        name_exists = await user_repo.check_display_name_exists(display_name)

        if name_exists:
            await message.answer(
                "❌ Это имя уже занято. Выбери другое:",
                reply_markup=None
            )
            return

        # Сохранение имени
        success = await user_repo.update_display_name(user_id, display_name)

        if not success:
            await message.answer(
                "❌ Ошибка сохранения имени. Попробуй еще раз:",
                reply_markup=None
            )
            return

        # Обновляем tutorial_step
        await client.execute_query(
            table="users",
            operation="update",
            data={"tutorial_step": TutorialStep.SHIPWRECK.value},
            filters={"user_id": user_id}
        )

        await message.answer(
            f"✅ Отлично, {display_name}! Твое имя сохранено.\n\n"
            "Теперь начнем историю...",
            reply_markup=get_tutorial_keyboard("shipwreck")
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка обработки имени в туториале: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка. Попробуй еще раз или обратись в поддержку.",
            reply_markup=None
        )


# НОВОЕ: Повтор ввода имени
@router.callback_query(F.data == "retry_display_name")
async def retry_display_name(callback: CallbackQuery, state: FSMContext):
    """Повтор ввода имени"""
    text = (
        f"📝 **Введите другое имя**\n\n"
        f"Требования:\n"
        f"• От 3 до 20 символов\n"
        f"• Имя должно быть уникальным\n\n"
        f"Введите новое имя:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_display_name")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)

    from interfaces.telegram_bot.states import TutorialState
    await state.set_state(TutorialState.WAITING_FOR_DISPLAY_NAME)
    await callback.answer()


# НОВОЕ: Пропуск ввода имени
@router.callback_query(F.data == "skip_display_name")
async def skip_display_name(callback: CallbackQuery, state: FSMContext):
    """Пропуск ввода имени"""
    await state.clear()

    text = (
        f"⏭️ **Имя не установлено**\n\n"
        f"Вы сможете изменить его позже в настройках.\n\n"
        f"🌊 Начинаем ваше приключение...\n\n"
        f"Вы просыпаетесь на берегу после кораблекрушения..."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_TUTORIAL_START, callback_data="tutorial_shipwreck")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("Имя можно будет изменить в настройках")

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
    """Продать осколок в ломбарде"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        logger.info(f"🔧 Начало продажи осколка для {user_id}")

        # Получаем клиент БД напрямую
        from adapters.database.supabase.client import get_supabase_client
        client = await get_supabase_client()

        # Получаем текущие данные пользователя
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["ryabucks", "golden_shards"],
            filters={"user_id": user_id},
            single=True
        )

        if not user_data:
            logger.error(f"❌ Пользователь {user_id} не найден в БД")
            await callback.answer("Ошибка: пользователь не найден", show_alert=True)
            return

        logger.info(f"📊 Текущие данные: ryabucks={user_data['ryabucks']}, golden_shards={user_data['golden_shards']}")

        # Проверяем наличие осколка
        current_shards = user_data.get('golden_shards', 0)
        if current_shards < 1:
            logger.warning(f"⚠️ У пользователя {user_id} нет осколков: {current_shards}")
            await callback.answer("У вас нет золотого осколка!", show_alert=True)
            return

        # Обновляем ресурсы
        new_ryabucks = user_data['ryabucks'] + 500
        new_shards = current_shards - 1

        logger.info(
            f"💰 Обновление: ryabucks {user_data['ryabucks']} → {new_ryabucks}, shards {current_shards} → {new_shards}")

        result = await client.execute_query(
            table="users",
            operation="update",
            data={
                "ryabucks": new_ryabucks,
                "golden_shards": new_shards
            },
            filters={"user_id": user_id}
        )

        if not result:
            logger.error(f"❌ Не удалось обновить данные пользователя {user_id}")
            await callback.answer("Ошибка обновления данных", show_alert=True)
            return

        logger.info(f"✅ Ресурсы успешно обновлены для {user_id}")

        # Логируем в блокчейн
        from services.blockchain_service import blockchain_service
        await blockchain_service.log_action(
            "SHARD_SOLD", user_id, username,
            {"shard_type": "golden", "price": 500, "currency": "ryabucks"},
            significance=1
        )

        logger.info(f"✅ Действие залогировано в блокчейн")

        # Обновляем шаг туториала
        from services.tutorial_service import tutorial_service
        from core.domain.entities import TutorialStep
        await tutorial_service.update_tutorial_step(user_id, TutorialStep.TOWN_HALL_REGISTER)

        logger.info(f"✅ Шаг туториала обновлен")

        # Показываем результат
        from config.texts import TUTORIAL_PAWNSHOP_SOLD
        await callback.message.edit_text(
            TUTORIAL_PAWNSHOP_SOLD,
            reply_markup=get_tutorial_keyboard("pawnshop_sold")
        )

        await callback.answer("✅ Осколок продан за 500 рябаксов!", show_alert=True)
        logger.info(f"🎉 Продажа осколка завершена успешно для {user_id}")

    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА продажи осколка для {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer(f"Ошибка продажи: {str(e)}", show_alert=True)


# Добавьте этот handler после функции tutorial_sell_shard:

@router.callback_query(F.data == "tutorial_townhall")
async def tutorial_townhall(callback: CallbackQuery):
    """Переход в ратушу"""
    try:
        user_id = callback.from_user.id

        # Обновляем шаг туториала
        await tutorial_service.update_tutorial_step(user_id, TutorialStep.TOWN_HALL_REGISTER)

        # Показываем ратушу
        await callback.message.edit_text(
            TUTORIAL_TOWNHALL_REGISTER,
            reply_markup=get_tutorial_keyboard("townhall_register")
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка перехода в ратушу: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "tutorial_register")
async def tutorial_register(callback: CallbackQuery):
    """Регистрация в ратуше - УПРОЩЕННАЯ ВЕРСИЯ"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        logger.info(f"=== НАЧАЛО РЕГИСТРАЦИИ для {user_id} ===")

        # Шаг 1: Получаем клиент
        from adapters.database.supabase.client import get_supabase_client
        client = await get_supabase_client()
        logger.info("✓ Клиент получен")

        # Шаг 2: Читаем данные
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["ryabucks"],
            filters={"user_id": user_id},
            single=True
        )
        logger.info(f"✓ Данные получены: ryabucks={user_data.get('ryabucks') if user_data else 'None'}")

        if not user_data:
            logger.error("✗ Пользователь не найден")
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        # Шаг 3: Проверяем деньги
        if user_data['ryabucks'] < 10:
            logger.warning(f"✗ Недостаточно денег: {user_data['ryabucks']}")
            await callback.answer(f"Недостаточно рябаксов! У вас {user_data['ryabucks']}, нужно 10.", show_alert=True)
            return

        logger.info("✓ Денег достаточно")

        # Шаг 4: Обновляем БД
        new_ryabucks = user_data['ryabucks'] - 10
        logger.info(f"Обновление: ryabucks {user_data['ryabucks']} → {new_ryabucks}")

        result = await client.execute_query(
            table="users",
            operation="update",
            data={
                "ryabucks": new_ryabucks
            },
            filters={"user_id": user_id}
        )
        logger.info(f"✓ БД обновлена: {bool(result)}")

        # Шаг 5: Обновляем шаг туториала
        from services.tutorial_service import tutorial_service
        from core.domain.entities import TutorialStep

        await tutorial_service.update_tutorial_step(user_id, TutorialStep.EMPLOYER_LICENSE)
        logger.info("✓ Шаг туториала обновлен")

        # Шаг 6: Показываем результат (БЕЗ format!)
        simple_text = f"""
✅ ВЫ ГРАЖДАНИН ОСТРОВА!

Поздравляю, гражданин @{username}!

💰 Потрачено: 10 рябаксов
"""

        await callback.message.edit_text(
            simple_text,
            reply_markup=get_tutorial_keyboard("townhall_registered")
        )
        logger.info("✓ Сообщение отправлено")

        await callback.answer("✅ Вы стали гражданином!", show_alert=True)
        logger.info("=== РЕГИСТРАЦИЯ ЗАВЕРШЕНА ===")

    except Exception as e:
        logger.error(f"=== ОШИБКА РЕГИСТРАЦИИ ===")
        logger.error(f"Тип ошибки: {type(e).__name__}")
        logger.error(f"Текст ошибки: {str(e)}")
        logger.error(f"Traceback:", exc_info=True)
        await callback.answer(f"Ошибка: {type(e).__name__}", show_alert=True)


@router.callback_query(F.data == "tutorial_employer_license")
async def tutorial_employer_license(callback: CallbackQuery):
    """Показать информацию о лицензии работодателя"""
    try:
        await callback.message.edit_text(
            TUTORIAL_EMPLOYER_LICENSE,
            reply_markup=get_tutorial_keyboard("employer_license")
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "tutorial_buy_employer_license")
async def tutorial_buy_employer_license(callback: CallbackQuery):
    """Купить лицензию работодателя"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        # Получаем клиент БД
        client = await get_supabase_client()

        # Получаем текущие данные
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["ryabucks", "has_employer_license"],
            filters={"user_id": user_id},
            single=True
        )

        if not user_data:
            await callback.answer("Ошибка получения профиля", show_alert=True)
            return

        # Проверяем, нет ли уже лицензии
        if user_data.get('has_employer_license', False):
            await callback.answer("У вас уже есть эта лицензия!", show_alert=True)
            return

        # Проверяем деньги
        if user_data['ryabucks'] < 100:
            await callback.answer("Недостаточно рябаксов! Нужно 100.", show_alert=True)
            return

        # Покупаем лицензию
        new_ryabucks = user_data['ryabucks'] - 100
        await client.execute_query(
            table="users",
            operation="update",
            data={
                "ryabucks": new_ryabucks,
                "has_employer_license": True,
                "has_island_access": True
            },
            filters={"user_id": user_id}
        )

        # Логируем покупку
        await blockchain_service.log_action(
            "LICENSE_PURCHASED", user_id, username,
            {"license_type": "employer", "level": 1, "price": 100},
            significance=1
        )

        # Обновляем шаг туториала - теперь игрок может нанимать рабочих
        await tutorial_service.update_tutorial_step(user_id, TutorialStep.ISLAND_ACCESS_GRANTED)

        # Показываем результат
        await callback.message.edit_text(
            text=TUTORIAL_LICENSE_BOUGHT.format(remaining=new_ryabucks),
            parse_mode="Markdown"
        )

        await callback.answer("✅ Лицензия куплена!", show_alert=True)

    except Exception as e:
        logger.error(f"❌ Ошибка покупки лицензии: {e}", exc_info=True)
        await callback.answer("Ошибка покупки", show_alert=True)



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
            reply_markup=None
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