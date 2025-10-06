# interfaces/telegram_bot/handlers/inventory.py
"""
Handler меню рюкзака (инвентаря)
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config.texts import *
from adapters.database.supabase.client import get_supabase_client

router = Router()
logger = logging.getLogger(__name__)


def get_inventory_keyboard():
    """Клавиатура рюкзака - ТОЧНЫЕ НАЗВАНИЯ"""
    keyboard = [
        [InlineKeyboardButton(text=BTN_INVENTORY_WALLET, callback_data="inv_wallet"),
         InlineKeyboardButton(text=BTN_INVENTORY_PASSES, callback_data="inv_passes")],
        [InlineKeyboardButton(text=BTN_INVENTORY_PRODUCTS, callback_data="inv_products"),
         InlineKeyboardButton(text=BTN_INVENTORY_HARVEST, callback_data="inv_harvest")],
        [InlineKeyboardButton(text=BTN_INVENTORY_ANIMALS, callback_data="inv_animals"),
         InlineKeyboardButton(text=BTN_INVENTORY_SEEDS, callback_data="inv_seeds")],
        [InlineKeyboardButton(text=BTN_INVENTORY_RESOURCES, callback_data="inv_resources"),
         InlineKeyboardButton(text=BTN_INVENTORY_BOXES, callback_data="inv_boxes")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_inventory_data(user_id: int) -> dict:
    """Получить данные рюкзака"""
    try:
        client = await get_supabase_client()

        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["ryabucks", "rbtc"],
            filters={"user_id": user_id},
            single=True
        )

        if not user_data:
            return {
                "ryabucks": 0,
                "rbtc": 0,
                "storage_percent": 0,
                "storage_used": 0,
                "storage_total": 50000
            }

        # TODO: Получать реальную занятость склада
        storage_used = 0
        storage_total = 50000
        storage_percent = int((storage_used / storage_total) * 100) if storage_total > 0 else 0

        return {
            "ryabucks": user_data.get('ryabucks', 0),
            "rbtc": user_data.get('rbtc', 0),
            "storage_percent": storage_percent,
            "storage_used": storage_used,
            "storage_total": storage_total
        }

    except Exception as e:
        logger.error(f"Ошибка получения данных рюкзака: {e}")
        return {
            "ryabucks": 0,
            "rbtc": 0,
            "storage_percent": 0,
            "storage_used": 0,
            "storage_total": 50000
        }


async def show_inventory_menu(message: Message):
    """Показать меню рюкзака"""
    try:
        user_id = message.from_user.id

        inv_data = await get_inventory_data(user_id)
        inv_text = INVENTORY_MENU.format(**inv_data)

        await message.answer(
            inv_text,
            reply_markup=get_inventory_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка меню рюкзака: {e}")
        await message.answer(ERROR_GENERAL)


# === ОБРАБОТЧИКИ РАЗДЕЛОВ РЮКЗАКА ===

@router.callback_query(F.data == "inv_wallet")
async def inv_wallet(callback: CallbackQuery):
    """Кошелек - показываем заново"""
    try:
        user_id = callback.from_user.id

        inv_data = await get_inventory_data(user_id)
        inv_text = INVENTORY_MENU.format(**inv_data)

        await callback.message.edit_text(
            inv_text,
            reply_markup=get_inventory_keyboard()
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка кошелька: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "inv_passes")
async def inv_passes(callback: CallbackQuery):
    """Допуски"""
    try:
        # TODO: Получать реальные данные
        passes_data = {
            "expedition_passes": 0,
            "anomaly_passes": 0,
            "farm_passes": 0,
            "city_passes": 0,
            "forest_passes": 0,
            "sea_passes": 0,
            "fight_passes": 0,
            "race_passes": 0
        }

        passes_text = INVENTORY_PASSES.format(**passes_data)

        await callback.message.edit_text(
            passes_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_inventory")]
            ])
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка допусков: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("inv_"))
async def handle_inventory_section(callback: CallbackQuery):
    """Обработка остальных разделов рюкзака"""
    try:
        section = callback.data.split("_")[1]

        # Пропускаем уже обработанные
        if section in ["wallet", "passes"]:
            return

        # TODO: Заполнить реальными данными из БД
        default_data = {
            "eggs": 0, "milk": 0, "honey": 0, "fish": 0, "chicken_meat": 0,
            "chick_meat": 0, "pork": 0, "beef": 0, "veal": 0, "mutton": 0,
            "horse_meat": 0, "game_meat": 0, "grain": 0, "tomatoes": 0,
            "cucumbers": 0, "potatoes": 0, "carrots": 0, "grapes": 0,
            "chickens": 0, "roosters": 0, "chicks": 0, "cows": 0, "bulls": 0,
            "calves": 0, "pigs": 0, "piglets": 0, "sheep": 0, "lambs": 0,
            "bees": 0, "horses": 0, "foals": 0, "saplings": 0, "grain_seeds": 0,
            "tomato_seeds": 0, "cucumber_seeds": 0, "potato_seeds": 0,
            "carrot_seeds": 0, "grape_seeds": 0, "golden_eggs": 0,
            "golden_shards": 0, "feathers": 0, "beeswax": 0, "horse_hair": 0,
            "sheep_wool": 0, "bristles": 0, "leather": 0, "bones": 0,
            "manure": 0, "stone": 0, "wood": 0, "free_boxes": 0,
            "farm_boxes": 0, "work_boxes": 0, "rbtc_boxes": 0,
            "expedition_boxes": 0, "fight_boxes": 0, "race_boxes": 0,
            "pass_boxes": 0, "keys": 0
        }

        section_texts = {
            "products": INVENTORY_PRODUCTS,
            "harvest": INVENTORY_HARVEST,
            "animals": INVENTORY_ANIMALS,
            "seeds": INVENTORY_SEEDS,
            "resources": INVENTORY_RESOURCES,
            "boxes": INVENTORY_BOXES
        }

        section_text = section_texts.get(section, "")

        if section_text:
            formatted_text = section_text.format(**default_data)

            await callback.message.edit_text(
                formatted_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_inventory")]
                ])
            )
        else:
            await callback.message.edit_text(
                f"🎒 РЮКЗАК\n\n{SECTION_UNDER_DEVELOPMENT}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_inventory")]
                ])
            )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка раздела рюкзака: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data == "back_to_inventory")
async def back_to_inventory(callback: CallbackQuery):
    """Возврат в меню рюкзака"""
    try:
        user_id = callback.from_user.id

        inv_data = await get_inventory_data(user_id)
        inv_text = INVENTORY_MENU.format(**inv_data)

        await callback.message.edit_text(
            inv_text,
            reply_markup=get_inventory_keyboard()
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка возврата в рюкзак: {e}")
        await callback.answer("Ошибка", show_alert=True)
