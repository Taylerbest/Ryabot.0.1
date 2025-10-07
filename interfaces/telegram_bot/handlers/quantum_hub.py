# interfaces/telegram_bot/handlers/quantum_hub.py
"""
Quantum Hub Handler - Квантхаб
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from adapters.database.supabase.client import get_supabase_client
from config.texts import *

router = Router()
logger = logging.getLogger(__name__)


def get_quantum_hub_keyboard():
    """Клавиатура меню Квантхаба"""
    keyboard = [
        [
            InlineKeyboardButton(text="⚛️ Лаб. Оборудование", callback_data="qhub_lab_equipment")
        ],
        [
            InlineKeyboardButton(text="🪪 Квантовый Пропуск", callback_data="quantum_pass")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_town")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data == "town_quantumhub")
async def show_quantum_hub_menu(callback: CallbackQuery):
    """Показать меню Квантхаба"""
    try:
        user_id = callback.from_user.id

        # Получить энергию пользователя
        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["energy"],
            filters={"user_id": user_id},
            single=True
        )

        energy = user_data.get('energy', 0) if user_data else 0

        qhub_text = f"""〰️〰️ 🖥 КВАНТХАБ ℹ️ 🔋{energy} 〰️〰️

Это сияющий узел реальности, где гении «Рябота» препарируют сам космос. В мерцающих порталах парят незавершённые творения, пойманные в ловушку вне потока времени."""

        await callback.message.edit_text(
            qhub_text,
            reply_markup=get_quantum_hub_keyboard()
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка показа меню Квантхаба: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "qhub_lab_equipment")
async def show_lab_equipment(callback: CallbackQuery):
    """Показать Лабораторное оборудование"""
    try:
        equipment_text = f"""⚛️ Лабораторное Оборудование

{SECTION_UNDER_DEVELOPMENT}

Здесь будет доступно:
• Квантовые ускорители
• Хроно-стабилизаторы
• Генераторы реальности
• Временные якоря"""

        keyboard = [
            [
                InlineKeyboardButton(text="↩️ Назад", callback_data="town_quantumhub")
            ]
        ]

        await callback.message.edit_text(
            equipment_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка показа оборудования: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


logger.info("Quantum Hub handlers loaded")
