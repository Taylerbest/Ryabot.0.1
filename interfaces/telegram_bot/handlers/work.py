# interfaces/telegram_bot/handlers/work.py
"""
Handler для системы работ (Рябота)
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config.texts import *
from services.quest_service import quest_service
from services.blockchain_service import blockchain_service

router = Router()
logger = logging.getLogger(__name__)

def get_work_keyboard():
    """Клавиатура работ - 6 локаций в 2 колонки"""
    keyboard = [
        [InlineKeyboardButton(text=BTN_WORK_ANOMALIES, callback_data="work_anomalies"),
         InlineKeyboardButton(text=BTN_WORK_EXPEDITION, callback_data="work_expedition")],
        [InlineKeyboardButton(text=BTN_WORK_FARM, callback_data="work_farm"),
         InlineKeyboardButton(text=BTN_WORK_CITY, callback_data="work_city")],
        [InlineKeyboardButton(text=BTN_WORK_FOREST, callback_data="work_forest"),
         InlineKeyboardButton(text=BTN_WORK_SEA, callback_data="work_sea")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def show_work_menu(message: Message):
    """Показать меню работ"""
    try:
        user_id = message.from_user.id
        
        # Проверяем доступ к работам
        has_access = await quest_service.can_access_feature(user_id, "work_general")
        
        if not has_access:
            await message.answer(f"💼 *РЯБОТА*\n\n{SECTION_LOCKED}")
            return
        
        await message.answer(
            WORK_MENU_TITLE,
            reply_markup=get_work_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка меню работ: {e}")
        await message.answer(ERROR_GENERAL)

# === ОБРАБОТЧИКИ ЛОКАЦИЙ ===

@router.callback_query(F.data == "work_sea")
async def work_sea(callback: CallbackQuery):
    """Работы в море"""
    try:
        user_id = callback.from_user.id
        
        # Проверяем доступ к морским работам
        has_access = await quest_service.can_access_feature(user_id, "work_sea")
        
        if not has_access:
            await callback.message.edit_text(
                f"🌊 *РАБОТЫ В МОРЕ*\n\n{SECTION_LOCKED}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_work")]
                ])
            )
            await callback.answer()
            return
        
        # Показываем доступные работы в море
        keyboard = []
        
        # Проверяем текущее задание
        current_quest = await quest_service.get_current_quest(user_id)
        if current_quest and current_quest["quest_id"] == "first_work":
            # Показываем кнопку для первой работы
            keyboard.append([InlineKeyboardButton(
                text="🚢 Разгрузить улов (5⚡ → 50💵 + 25📊)", 
                callback_data="do_first_work"
            )])
        else:
            # Обычные работы (заглушка)
            keyboard.append([InlineKeyboardButton(
                text="🚧 Другие работы в разработке", 
                callback_data="work_unavailable"
            )])
        
        keyboard.append([InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_work")])
        
        await callback.message.edit_text(
            WORK_SEA_TITLE,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка морских работ: {e}")
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "do_first_work")
async def do_first_work(callback: CallbackQuery):
    """Выполнить первую работу"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or f"user_{user_id}"
        
        # Проверяем, доступна ли первая работа
        if not await quest_service.is_quest_available(user_id, "first_work"):
            await callback.answer("Эта работа сейчас недоступна", show_alert=True)
            return
        
        # Получаем профиль и проверяем энергию
        from .start import get_user_use_cases
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)
        
        if profile['energy'] < 5:
            await callback.answer(
                f"⚡ Недостаточно энергии! Нужно 5, у вас {profile['energy']}",
                show_alert=True
            )
            return
        
        # Выполняем работу
        await use_cases['update_resources'].execute(user_id, {
            "ryabucks": profile['ryabucks'] + 50,
            "experience": profile['experience'] + 25,
            "energy": max(0, profile['energy'] - 5)
        })
        
        # Логируем
        await blockchain_service.log_action(
            "WORK_COMPLETED", user_id, username,
            {"task": "sea_cargo_unload", "reward_money": 50, "reward_exp": 25, "energy_spent": 5},
            significance=0
        )
        
        # Завершаем задание
        await quest_service.complete_quest(user_id, "first_work")
        
        # Показываем результат
        await callback.message.edit_text(
            f"""
✅ *РАБОТА ВЫПОЛНЕНА!*

🚢 Вы помогли разгрузить рыболовное судно!

🎁 *Получено:*
💵 +50 рябаксов
📊 +25 опыта
⚡ -5 энергии

🎯 *Следующий шаг:* Получите дополнительный опыт у жителя!
Идите в 👤 Житель → 📋 Задания → "Получить опыт"
            """.strip(),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎉 Отлично!", callback_data="back_to_work")]
            ])
        )
        
        await callback.answer("✅ Работа выполнена!", show_alert=True)
        
    except Exception as e:
        logger.error(f"Ошибка выполнения первой работы: {e}")
        await callback.answer("Ошибка выполнения работы", show_alert=True)

# === ЗАГЛУШКИ ОСТАЛЬНЫХ ЛОКАЦИЙ ===

@router.callback_query(F.data.startswith("work_"))
async def work_location(callback: CallbackQuery):
    """Обработка остальных локаций работ"""
    try:
        location = callback.data.split("_")[1]
        
        location_names = {
            "anomalies": "⚠️ АНОМАЛИИ",
            "expedition": "🏕 ЭКСПЕДИЦИЯ", 
            "farm": "🏡 ФЕРМА",
            "city": "🏢 ГОРОД",
            "forest": "🌲 ЛЕС"
        }
        
        location_name = location_names.get(location, "НЕИЗВЕСТНАЯ ЛОКАЦИЯ")
        
        await callback.message.edit_text(
            f"{location_name}\n\n{SECTION_UNDER_DEVELOPMENT}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_work")]
            ])
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка локации работ: {e}")
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "work_unavailable")
async def work_unavailable(callback: CallbackQuery):
    """Недоступные работы"""
    await callback.answer("🚧 Эти работы пока в разработке!", show_alert=True)

@router.callback_query(F.data == "back_to_work")
async def back_to_work(callback: CallbackQuery):
    """Возврат в меню работ"""
    try:
        await callback.message.edit_text(
            WORK_MENU_TITLE,
            reply_markup=get_work_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка возврата в работы: {e}")
        await callback.answer("Ошибка", show_alert=True)