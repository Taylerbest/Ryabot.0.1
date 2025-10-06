# interfaces/telegram_bot/handlers/academy.py
"""
Handler для Академии - адаптированный под ваш проект
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config.texts import *
from services.quest_service import quest_service
from services.blockchain_service import blockchain_service
from adapters.database.supabase.client import get_supabase_client

router = Router()
logger = logging.getLogger(__name__)


def get_academy_keyboard():
    """Главное меню академии"""
    keyboard = [
        [InlineKeyboardButton(text=BTN_LABOR_EXCHANGE, callback_data="academy_hire")],
        [InlineKeyboardButton(text=BTN_EXPERT_COURSES, callback_data="academy_train")],
        [InlineKeyboardButton(text=BTN_TRAINING_CLASS, callback_data="academy_class")],
        [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_town")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_hire_keyboard(can_hire=True, worker_count=0):
    """Клавиатура найма рабочих"""
    if can_hire:
        cost = 30 + (worker_count * 10)  # Цена растет с количеством
        keyboard = [
            [InlineKeyboardButton(
                text=f"👷 Нанять рабочего ({cost} 💵)",
                callback_data=f"hire_worker_{cost}"
            )],
            [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_academy")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(text="⏳ Недостаточно средств", callback_data="hire_unavailable")],
            [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_academy")]
        ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_training_keyboard():
    """Клавиатура обучения специалистов"""
    keyboard = [
        [InlineKeyboardButton(text="👨‍🌾 Обучить фермера (25🧪 + 50💵)", callback_data="train_farmer")],
        [InlineKeyboardButton(text="🏗️ Обучить строителя (25🧪 + 50💵)", callback_data="train_builder")],
        [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_academy")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def show_academy_menu(callback: CallbackQuery):
    """Показать главное меню академии"""
    try:
        user_id = callback.from_user.id



        # Получаем статистику академии
        client = await get_supabase_client()
        specialists = await client.execute_query(
            table="specialists",
            operation="select",
            columns=["specialist_type"],
            filters={"user_id": user_id}
        )

        specialist_count = len(specialists) if specialists else 0

        academy_text = f"""
🎓 *АКАДЕМИЯ ОСТРОВА*

Центр обучения и найма специалистов.
Здесь вы можете нанимать рабочих и обучать их профессиям.

👥 *Ваши специалисты:* {specialist_count}
📚 *Доступные курсы:* Фермер, Строитель

💡 *Совет:* Специалисты работают эффективнее обычных рабочих!

👇 Выберите действие:
        """.strip()

        await callback.message.edit_text(
            academy_text,
            reply_markup=get_academy_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка академии: {e}")
        await callback.answer("Ошибка загрузки академии", show_alert=True)


# === ОБРАБОТЧИКИ АКАДЕМИИ ===

@router.callback_query(F.data == "academy_hire")
async def academy_hire(callback: CallbackQuery):
    """Биржа труда - найм рабочих"""
    try:
        user_id = callback.from_user.id



        # Получаем профиль пользователя
        from interfaces.telegram_bot.handlers.start import get_user_use_cases
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        # Считаем количество рабочих
        client = await get_supabase_client()
        workers = await client.execute_query(
            table="specialists",
            operation="select",
            columns=["id"],
            filters={"user_id": user_id}
        )

        worker_count = len(workers) if workers else 0
        hire_cost = 30 + (worker_count * 10)
        can_hire = profile['ryabucks'] >= hire_cost

        hire_text = f"""
💼 *БИРЖА ТРУДА*

Наймите рабочих для выполнения различных задач на острове.

👥 *Ваши рабочие:* {worker_count}
💰 *Стоимость найма:* {hire_cost} рябаксов
💵 *Ваши средства:* {profile['ryabucks']} рябаксов

{"✅ Вы можете нанять рабочего!" if can_hire else "❌ Недостаточно средств для найма"}
        """.strip()

        await callback.message.edit_text(
            hire_text,
            reply_markup=get_hire_keyboard(can_hire, worker_count)
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка биржи труда: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("hire_worker_"))
async def hire_worker(callback: CallbackQuery):
    """Нанять рабочего"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        # Извлекаем стоимость
        cost = int(callback.data.split("_")[-1])

        # Проверяем доступность найма
        if not await quest_service.is_quest_available(user_id, "hire_worker"):
            await callback.answer("Это действие сейчас недоступно", show_alert=True)
            return

        # Проверяем средства
        from interfaces.telegram_bot.handlers.start import get_user_use_cases
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        if profile['ryabucks'] < cost:
            await callback.answer(f"Недостаточно средств! Нужно {cost} рябаксов", show_alert=True)
            return

        # Создаем рабочего
        client = await get_supabase_client()
        worker_data = {
            "user_id": user_id,
            "specialist_type": "worker",
            "level": 1,
            "experience": 0,
            "status": "idle",
            "hp": 25,
            "stamina": 25
        }

        await client.execute_query(
            table="specialists",
            operation="insert",
            data=worker_data,
            single=True
        )

        # Списываем деньги
        await use_cases['update_resources'].execute(user_id, {
            "ryabucks": profile['ryabucks'] - cost
        })

        # Логируем
        await blockchain_service.log_action(
            "WORKER_HIRED", user_id, username,
            {"name": "Рабочий", "cost": cost},
            significance=1
        )

        # Завершаем задание
        await quest_service.complete_quest(user_id, "hire_worker")

        # Показываем результат
        await callback.message.edit_text(
            f"""
✅ *РАБОЧИЙ НАНЯТ!*

🎉 Поздравляем! Вы наняли своего первого рабочего!

👷 *Имя:* Рабочий #{user_id % 1000}
💰 *Потрачено:* {cost} рябаксов
💪 *Статус:* Готов к работе

🎯 *Следующий шаг:* Отправьте рабочего на первую работу!
Идите в 💼 Рябота → 🌊 Море → "Разгрузить улов"
            """.strip(),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎉 Отлично!", callback_data="back_to_academy")]
            ])
        )

        await callback.answer("✅ Рабочий нанят!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка найма рабочего: {e}")
        await callback.answer("Ошибка найма", show_alert=True)


@router.callback_query(F.data == "academy_train")
async def academy_train(callback: CallbackQuery):
    """Курсы экспертов - обучение специалистов"""
    try:
        user_id = callback.from_user.id


        # Получаем профиль
        from interfaces.telegram_bot.handlers.start import get_user_use_cases
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        # Проверяем наличие рабочих
        client = await get_supabase_client()
        workers = await client.execute_query(
            table="specialists",
            operation="select",
            columns=["id", "specialist_type"],
            filters={"user_id": user_id, "specialist_type": "worker"}
        )

        if not workers:
            await callback.message.edit_text(
                f"""
🎓 *КУРСЫ ЭКСПЕРТОВ*

❌ У вас нет рабочих для обучения!

Сначала наймите рабочего в 💼 Бирже труда.
                """.strip(),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_academy")]
                ])
            )
            await callback.answer()
            return

        train_text = f"""
🎓 *КУРСЫ ЭКСПЕРТОВ*

Обучите ваших рабочих профессиям для повышения эффективности.

👷 *Доступно для обучения:* {len(workers)} рабочих

💰 *Ваши ресурсы:*
💵 {profile['ryabucks']} рябаксов
🧪 {profile['liquid_experience']} жидкого опыта

📚 *Доступные курсы:*
        """.strip()

        await callback.message.edit_text(
            train_text,
            reply_markup=get_training_keyboard()
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка курсов: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("train_"))
async def train_specialist(callback: CallbackQuery):
    """Обучить специалиста"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"

        specialty = callback.data.split("_")[1]  # farmer или builder

        # Проверяем доступность обучения
        if not await quest_service.is_quest_available(user_id, "train_specialist"):
            await callback.answer("Это действие сейчас недоступно", show_alert=True)
            return

        # Получаем профиль
        from interfaces.telegram_bot.handlers.start import get_user_use_cases
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        # Проверяем ресурсы
        if profile['liquid_experience'] < 25 or profile['ryabucks'] < 50:
            await callback.answer(
                f"Недостаточно ресурсов! Нужно 25 жидкого опыта и 50 рябаксов",
                show_alert=True
            )
            return

        # Обновляем специалиста
        client = await get_supabase_client()
        await client.execute_query(
            table="specialists",
            operation="update",
            data={"specialist_type": specialty},
            filters={"user_id": user_id, "specialist_type": "worker"}
        )

        # Списываем ресурсы
        await use_cases['update_resources'].execute(user_id, {
            "liquid_experience": profile['liquid_experience'] - 25,
            "ryabucks": profile['ryabucks'] - 50
        })

        # Логируем
        await blockchain_service.log_action(
            "SPECIALIST_TRAINED", user_id, username,
            {"specialty": specialty, "cost_exp": 25, "cost_money": 50},
            significance=1
        )

        # Завершаем задание
        await quest_service.complete_quest(user_id, "train_specialist")

        # Показываем результат
        specialty_name = SPECIALTY_FARMER if specialty == "farmer" else SPECIALTY_BUILDER
        abilities = SPECIALTY_ABILITIES[specialty]

        await callback.message.edit_text(
            f"""
✅ *СПЕЦИАЛИСТ ОБУЧЕН!*

🎓 Ваш рабочий успешно освоил профессию {specialty_name}!

💪 *Новые способности:*
{abilities}

🎯 *Следующий шаг:* Купите фермерскую лицензию в Ратуше!
Идите в 🏘️ Город → 🏛️ Ратуша → Лицензии
            """.strip(),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎉 Отлично!", callback_data="back_to_academy")]
            ])
        )

        await callback.answer("🎓 Специалист обучен!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка обучения: {e}")
        await callback.answer("Ошибка обучения", show_alert=True)


@router.callback_query(F.data == "academy_class")
async def academy_class(callback: CallbackQuery):
    """Класс обучения (заглушка)"""
    await callback.message.edit_text(
        f"📚 *КЛАСС ОБУЧЕНИЯ*\n\n{SECTION_UNDER_DEVELOPMENT}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_academy")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "hire_unavailable")
async def hire_unavailable(callback: CallbackQuery):
    """Найм недоступен"""
    await callback.answer("Недостаточно средств для найма рабочего", show_alert=True)


@router.callback_query(F.data == "back_to_academy")
async def back_to_academy(callback: CallbackQuery):
    """Возврат в академию"""
    await show_academy_menu(callback)