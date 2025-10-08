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


from utils.base62_helper import generate_referral_link


async def get_friends_data(user_id: int) -> dict:
    """Получить данные о друзьях и рефералах (3 уровня)"""
    from adapters.database.supabase.client import get_supabase_client
    from utils.base62_helper import generate_referral_link
    from config.settings import settings

    client = await get_supabase_client()

    # 1. Получаем player_id для реф-ссылки
    user_data_raw = await client.execute_query(
        table="users",
        operation="select",
        columns=["player_id"],
        filters={"user_id": user_id},
        single=True
    )

    if isinstance(user_data_raw, list):
        user_data = user_data_raw[0] if user_data_raw else None
    else:
        user_data = user_data_raw

    player_id = user_data.get("player_id") if user_data else user_id
    referral_link = generate_referral_link(player_id, settings.BOT_USERNAME)

    # 2. УРОВЕНЬ 1: Друзья (прямые рефералы)
    level1_raw = await client.execute_query(
        table="referrals",
        operation="select",
        columns=["referred_user_id"],
        filters={"referrer_user_id": user_id, "is_active": True}
    )

    level1 = level1_raw if isinstance(level1_raw, list) else ([level1_raw] if level1_raw else [])
    friends_ids = [r["referred_user_id"] for r in level1]
    friends_count = len(friends_ids)

    # 3. УРОВЕНЬ 2: Знакомые (рефералы друзей)
    acquaintances_count = 0
    acquaintances_ids = []

    if friends_ids:
        level2_raw = await client.execute_query(
            table="referrals",
            operation="select",
            columns=["referred_user_id"],
            filters={"referrer_user_id": {"in": friends_ids}, "is_active": True}
        )

        level2 = level2_raw if isinstance(level2_raw, list) else ([level2_raw] if level2_raw else [])
        acquaintances_ids = [r["referred_user_id"] for r in level2]
        acquaintances_count = len(acquaintances_ids)

    # 4. УРОВЕНЬ 3: Окружение (рефералы знакомых)
    network_count = 0

    if acquaintances_ids:
        level3_raw = await client.execute_query(
            table="referrals",
            operation="select",
            columns=["referred_user_id"],
            filters={"referrer_user_id": {"in": acquaintances_ids}, "is_active": True}
        )

        level3 = level3_raw if isinstance(level3_raw, list) else ([level3_raw] if level3_raw else [])
        network_count = len(level3)

    return {
        "user_id": user_id,
        "referral_link": referral_link,
        "ref_rbtc": 0,
        "ref_ryabucks": 0,
        "ref_tickets": 0,
        "total_rbtc": 0,
        "total_ryabucks": 0,
        "total_tickets": 0,
        "friends_count": friends_count,  # Уровень 1
        "acquaintances_count": acquaintances_count,  # Уровень 2
        "network_count": network_count,  # Уровень 3
        "partner_pool": 4_200_000,
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
