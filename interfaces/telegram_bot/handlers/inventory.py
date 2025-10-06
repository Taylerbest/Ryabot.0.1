# interfaces/telegram_bot/handlers/inventory.py

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config.texts import *
from adapters.database.supabase.client import get_supabase_client

router = Router()
logger = logging.getLogger(__name__)


def get_inventory_keyboard(selected_section="wallet"):
    """
    Клавиатура рюкзака с динамическим индикатором в два столбца
    selected_section - текущий выбранный раздел
    """
    sections = [
        ("wallet", "💰 Кошелек"),
        ("passes", "🎫 Допуски"),
        ("products", "🥚 Продукты"),
        ("harvest", "🥕 Урожай"),
        ("animals", "🐮 Животные"),
        ("seeds", "🍃 Семена"),
        ("resources", "🪵 Ресурсы"),
        ("boxes", "📦 Коробки")
    ]

    keyboard = []
    row = []

    # Создаем кнопки по две в ряд
    for section_key, section_name in sections:
        if section_key == selected_section:
            button_text = f"👉{section_name}"
        else:
            button_text = section_name

        row.append(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"inventory_{section_key}"
            )
        )

        # Когда в ряду 2 кнопки, добавляем ряд в клавиатуру
        if len(row) == 2:
            keyboard.append(row)
            row = []

    # Если осталась одна кнопка, добавляем её
    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_inventory_data(user_id: int) -> dict:
    """Получить данные инвентаря пользователя"""
    try:
        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            filters={"user_id": user_id},
            single=True
        )

        if not user_data:
            return {}

        # Здесь добавьте получение данных из других таблиц
        # (animals, resources, items и т.д.)

        return {
            "ryabucks": user_data.get('ryabucks', 0),
            "rbtc": user_data.get('rbtc', 0),
            "storage_used": 0,  # TODO: рассчитать реально
            "storage_total": 1000,
            "storage_percent": 0,

            # Допуски
            "expedition_passes": 0,
            "anomaly_passes": 0,
            "farm_passes": 0,
            "city_passes": 0,
            "forest_passes": 0,
            "sea_passes": 0,
            "fight_passes": 0,
            "race_passes": 0,

            # Продукты
            "eggs": 0,
            "milk": 0,
            "honey": 0,
            "fish": 0,
            "chicken_meat": 0,
            "chick_meat": 0,
            "pork": 0,
            "beef": 0,
            "veal": 0,
            "mutton": 0,
            "horse_meat": 0,
            "game_meat": 0,

            # Урожай
            "grain": 0,
            "tomatoes": 0,
            "cucumbers": 0,
            "potatoes": 0,
            "carrots": 0,
            "grapes": 0,

            # Животные
            "chickens": 0,
            "roosters": 0,
            "chicks": 0,
            "cows": 0,
            "bulls": 0,
            "calves": 0,
            "pigs": 0,
            "piglets": 0,
            "sheep": 0,
            "lambs": 0,
            "bees": 0,
            "horses": 0,
            "foals": 0,

            # Семена
            "saplings": 0,
            "grain_seeds": 0,
            "tomato_seeds": 0,
            "cucumber_seeds": 0,
            "potato_seeds": 0,
            "carrot_seeds": 0,
            "grape_seeds": 0,

            # Ресурсы
            "golden_eggs": 0,
            "golden_shards": user_data.get('golden_shards', 0),
            "feathers": 0,
            "beeswax": 0,
            "horse_hair": 0,
            "sheep_wool": 0,
            "bristles": 0,
            "leather": 0,
            "bones": 0,
            "manure": 0,
            "stone": 0,
            "wood": user_data.get('wood', 0),

            # Коробки
            "free_boxes": 0,
            "farm_boxes": 0,
            "work_boxes": 0,
            "rbtc_boxes": 0,
            "expedition_boxes": 0,
            "fight_boxes": 0,
            "race_boxes": 0,
            "pass_boxes": 0,
            "keys": user_data.get('golden_keys', 0)
        }

    except Exception as e:
        logger.error(f"Ошибка получения инвентаря: {e}")
        return {}


async def get_inventory_text(section: str, data: dict) -> str:
    """Получить текст для выбранного раздела"""
    texts = {
        "wallet": INVENTORY_MENU.format(**data),
        "passes": INVENTORY_PASSES.format(**data),
        "products": INVENTORY_PRODUCTS.format(**data),
        "harvest": INVENTORY_HARVEST.format(**data),
        "animals": INVENTORY_ANIMALS.format(**data),
        "seeds": INVENTORY_SEEDS.format(**data),
        "resources": INVENTORY_RESOURCES.format(**data),
        "boxes": INVENTORY_BOXES.format(**data)
    }

    return texts.get(section, "Раздел не найден")


async def show_inventory_menu(message: Message, section="wallet"):
    """Показать меню рюкзака"""
    try:
        user_id = message.from_user.id
        data = await get_inventory_data(user_id)
        text = await get_inventory_text(section, data)

        await message.answer(
            text,
            reply_markup=get_inventory_keyboard(section)
        )

    except Exception as e:
        logger.error(f"Ошибка меню рюкзака: {e}")
        await message.answer(ERROR_GENERAL)


# === ОБРАБОТЧИКИ ===

@router.message(F.text == BTN_INVENTORY)
async def inventory_handler(message: Message):
    """Открыть рюкзак (кошелек по умолчанию)"""
    await show_inventory_menu(message, section="wallet")


@router.callback_query(F.data.startswith("inventory_"))
async def inventory_section_handler(callback: CallbackQuery):
    """Переключение между разделами рюкзака"""
    try:
        section = callback.data.replace("inventory_", "")
        user_id = callback.from_user.id

        data = await get_inventory_data(user_id)
        text = await get_inventory_text(section, data)

        await callback.message.edit_text(
            text,
            reply_markup=get_inventory_keyboard(section)
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка переключения раздела: {e}")
        await callback.answer("Ошибка", show_alert=True)
