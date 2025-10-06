"""
Обработчик команды /map - мгновенное открытие WebApp
"""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

logger = logging.getLogger(__name__)

router = Router()

ISLAND_MAP_URL = "https://taylerbest.github.io/ryabot/"

@router.message(Command("map"))
async def cmd_map(message: Message):
    """Быстрое открытие карты - только кнопка"""
    try:
        # Создаем inline кнопку
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🗺️ Открыть карту острова",
                web_app=WebAppInfo(url=ISLAND_MAP_URL)
            )]
        ])

        # Минимальное сообщение
        await message.answer(
            text="🗺️ <b>Карта острова</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("❌ Ошибка")
