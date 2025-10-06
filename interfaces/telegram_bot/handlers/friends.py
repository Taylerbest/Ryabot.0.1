# interfaces/telegram_bot/handlers/friends.py
"""
Handler меню друзей
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import LinkPreviewOptions
from config.texts import *
from config.settings import settings

router = Router()
logger = logging.getLogger(__name__)


def get_friends_keyboard():
    """Клавиатура друзей - ТОЧНЫЕ НАЗВАНИЯ"""
    keyboard = [
        [InlineKeyboardButton(text=BTN_FRIENDS_MY, callback_data="friends_my")],
        [InlineKeyboardButton(text=BTN_FRIENDS_STORAGE, callback_data="friends_storage")],
        [InlineKeyboardButton(text=BTN_FRIENDS_SHOP, callback_data="friends_shop")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_friends_data(user_id: int) -> dict:
    """Получить данные реферальной системы"""
    # TODO: Получать реальные данные из БД

    referral_link = f"https://t.me/{settings.BOT_USERNAME}?start=ref{user_id}"

    return {
        "user_id": user_id,
        "referral_link": referral_link,
        "ref_rbtc": 0,
        "ref_ryabucks": 0,
        "ref_tickets": 0,
        "total_rbtc": 0,
        "total_ryabucks": 0,
        "total_tickets": 0,
        "friends_count": 0,
        "acquaintances_count": 0,
        "network_count": 0,
        "partner_pool": 4200000,
        "partner_rating": 0
    }


async def show_friends_menu(message: Message):
    """Показать меню друзей"""
    try:
        user_id = message.from_user.id

        friends_data = await get_friends_data(user_id)
        friends_text = FRIENDS_MENU.format(**friends_data)

        await message.answer(
            friends_text,
            reply_markup=get_friends_keyboard(),
            parse_mode=None,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )

    except Exception as e:
        logger.error(f"Ошибка меню друзей: {e}")
        await message.answer(ERROR_GENERAL)


# === ОБРАБОТЧИКИ РАЗДЕЛОВ ДРУЗЕЙ ===

@router.callback_query(F.data.startswith("friends_"))
async def handle_friends_section(callback: CallbackQuery):
    """Обработка разделов друзей"""
    try:
        section = callback.data.split("_")[1]

        section_names = {
            "my": "👥 МОИ ДРУЗЬЯ",
            "storage": "🪙 ХРАНИЛИЩЕ",
            "shop": "🎟 МАГАЗИН"
        }

        section_name = section_names.get(section, "НЕИЗВЕСТНЫЙ РАЗДЕЛ")

        await callback.message.edit_text(
            f"{section_name}\n\n{SECTION_UNDER_DEVELOPMENT}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_friends")]
            ])
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка раздела друзей: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "back_to_friends")
async def back_to_friends(callback: CallbackQuery):
    """Возврат в меню друзей"""
    try:
        user_id = callback.from_user.id

        friends_data = await get_friends_data(user_id)
        friends_text = FRIENDS_MENU.format(**friends_data)

        await callback.message.edit_text(
            friends_text,
            reply_markup=get_friends_keyboard(),
            parse_mode=None,
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка возврата в друзья: {e}")
        await callback.answer("Ошибка", show_alert=True)
