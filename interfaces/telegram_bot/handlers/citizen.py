# interfaces/telegram_bot/handlers/citizen.py
"""
Handler меню жителя
"""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config.texts import *
from services.quest_service import quest_service
from adapters.database.supabase.client import get_supabase_client

router = Router()
logger = logging.getLogger(__name__)


def get_citizen_keyboard():
    """Клавиатура жителя - ТОЧНЫЕ НАЗВАНИЯ"""
    keyboard = [
        [InlineKeyboardButton(text=BTN_CITIZEN_PROPERTIES, callback_data="citizen_properties"),
         InlineKeyboardButton(text=BTN_CITIZEN_WARDROBE, callback_data="citizen_wardrobe")],
        [InlineKeyboardButton(text=BTN_CITIZEN_HISTORY, callback_data="citizen_history"),
         InlineKeyboardButton(text=BTN_CITIZEN_TASKS, callback_data="citizen_tasks")],
        [InlineKeyboardButton(text=BTN_CITIZEN_ACHIEVEMENTS, callback_data="citizen_achievements"),
         InlineKeyboardButton(text=BTN_CITIZEN_STATISTICS, callback_data="citizen_statistics")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_citizen_data(user_id: int) -> dict:
    """Получить данные жителя"""
    try:
        client = await get_supabase_client()

        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["username", "created_at", "has_employer_license", "liquid_experience", "level"],
            filters={"user_id": user_id},
            single=True
        )

        if not user_data:
            return {}

        # Форматируем дату регистрации
        created_at = user_data.get('created_at', '2024-01-01')
        if isinstance(created_at, str):
            registration_date = created_at[:10].replace('-', '.')
        else:
            registration_date = "01.01.2024"

        return {
            "username": user_data.get('username', 'user'),
            "registration_date": registration_date,
            "farmer_rank": "—",
            "employer_rank": "—",
            "trader_rank": "—",
            "burner_rank": "—",
            "explorer_rank": "—",
            "gambler_rank": "—",
            "racer_rank": "—",
            "fighter_rank": "—",
            "partner_rank": "—",
            "liquid_experience": user_data.get('liquid_experience', 0),
            "q_points": 0  # TODO: Добавить в БД
        }

    except Exception as e:
        logger.error(f"Ошибка получения данных жителя: {e}")
        return {}


async def show_citizen_menu(message: Message):
    """Показать меню жителя"""
    try:
        user_id = message.from_user.id

        # Получаем данные жителя
        citizen_data = await get_citizen_data(user_id)

        if not citizen_data:
            await message.answer("❌ Ошибка получения данных")
            return

        # Формируем текст меню
        citizen_text = CITIZEN_MENU.format(**citizen_data)

        await message.answer(
            citizen_text,
            reply_markup=get_citizen_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка меню жителя: {e}")
        await message.answer(ERROR_GENERAL)


# === ОБРАБОТЧИКИ РАЗДЕЛОВ ЖИТЕЛЯ ===

@router.callback_query(F.data == "citizen_tasks")
async def citizen_tasks(callback: CallbackQuery):
    try:
        userid = callback.from_user.id

        from services.questservice import questservice
        from adapters.database.supabase.client import get_supabase_client
        client = await get_supabase_client()

        # Получаем текущий шаг туториала
        userdata = await client.execute_query(
            table="users",
            operation="select",
            columns=["tutorialstep", "tutorialcompleted"],
            filters={"userid": userid},
            single=True
        )

        if not userdata:
            await callback.answer("❌ Ошибка", show_alert=True)
            return

        tutorialstep = TutorialStep(userdata.get("tutorialstep", "notstarted"))
        tutorial_completed = userdata.get("tutorialcompleted", False)

        # ИСПРАВЛЕНИЕ: Показываем квест "Начало" если туториал не завершён
        if not tutorial_completed:
            # Квест "Начало" включает весь путь до покупки первой курицы
            quest_stages = {
                TutorialStep.ISLANDACCESSGRANTED: "✅ Получен доступ на остров\n⏳ Наймите работника в Академии",
                TutorialStep.TASKHIREWORKER: "✅ Доступ на остров\n⏳ Наймите работника за 30 рябаксов",
                TutorialStep.TASKFIRSTWORK: "✅ Работник нанят\n⏳ Выполните первую работу в море",
                TutorialStep.TASKCITIZENQUEST: "✅ Первая работа выполнена\n⏳ Посетите ратушу",
                TutorialStep.TASKTRAINSPECIALIST: "✅ Зарегистрированы в ратуше\n⏳ Обучите специалиста",
                TutorialStep.TASKBUYFARMLICENSE: "✅ Специалист обучен\n⏳ Купите фермерскую лицензию",
                TutorialStep.TASKBUYLAND: "✅ Лицензия получена\n⏳ Купите участок земли",
                TutorialStep.TASKBUILDCROPBED: "✅ Земля куплена\n⏳ Постройте грядку",
                TutorialStep.TASKPLANTGRAIN: "✅ Грядка построена\n⏳ Посадите зерно",
                TutorialStep.TASKBUILDHENHOUSE: "✅ Зерно посажено\n⏳ Постройте курятник",
                TutorialStep.TASKBUYCHICKEN: "✅ Курятник построен\n⏳ Купите первую курицу в магазине"
            }

            progress_text = quest_stages.get(
                tutorialstep,
                "⏳ Продолжайте выполнять задания"
            )

            quest_text = f"""📝 ЗАДАНИЕ: НАЧАЛО

🎯 Цель: Обустроить свою ферму на острове

{progress_text}

💰 Награда: 200 рябаксов, 100 опыта при полном выполнении"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="backtocitizen")]
            ])

            await callback.message.edit_text(quest_text, reply_markup=keyboard)
            await callback.answer()
            return

        # Если туториал завершён, показываем другие задания или сообщение
        quest_text = """📝 ЗАДАНИЯ

🎉 Поздравляем! Все базовые задания выполнены!

Продолжайте развивать свою ферму и исследовать остров."""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="backtocitizen")]
        ])

        await callback.message.edit_text(quest_text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Citizen tasks error: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("citizen_"))
async def handle_citizen_section(callback: CallbackQuery):
    """Обработка остальных разделов жителя"""
    try:
        section = callback.data.split("_")[1]

        # Пропускаем "tasks" - он обработан выше
        if section == "tasks":
            return

        section_names = {
            "properties": "🏞 ВЛАДЕНИЯ",
            "wardrobe": "🥼 ГАРДЕРОБ",
            "history": "📖 ИСТОРИЯ",
            "achievements": "🎯 ДОСТИЖЕНИЯ",
            "statistics": "📊 СТАТИСТИКА"
        }

        section_name = section_names.get(section, "НЕИЗВЕСТНЫЙ РАЗДЕЛ")

        await callback.message.edit_text(
            f"{section_name}\n\n{SECTION_UNDER_DEVELOPMENT}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_citizen")]
            ])
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка раздела жителя: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "back_to_citizen")
async def back_to_citizen(callback: CallbackQuery):
    """Возврат в меню жителя"""
    try:
        user_id = callback.from_user.id

        citizen_data = await get_citizen_data(user_id)

        if not citizen_data:
            await callback.answer("Ошибка", show_alert=True)
            return

        citizen_text = CITIZEN_MENU.format(**citizen_data)

        await callback.message.edit_text(
            citizen_text,
            reply_markup=get_citizen_keyboard()
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка возврата к жителю: {e}")
        await callback.answer("Ошибка", show_alert=True)
