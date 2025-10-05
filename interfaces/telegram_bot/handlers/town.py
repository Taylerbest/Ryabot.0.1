# interfaces/telegram_bot/handlers/town.py
"""
Handler города с правильной архитектурой
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config.texts import *
from services.tutorial_service import tutorial_service

router = Router()
logger = logging.getLogger(__name__)

def get_town_keyboard():
    """Клавиатура города - 14 зданий в 2 колонки"""
    keyboard = [
        # Строка 1
        [InlineKeyboardButton(text=BTN_TOWNHALL, callback_data="building_townhall"),
         InlineKeyboardButton(text=BTN_MARKET, callback_data="building_market")],
        # Строка 2  
        [InlineKeyboardButton(text=BTN_ACADEMY, callback_data="building_academy"),
         InlineKeyboardButton(text=BTN_RYABANK, callback_data="building_ryabank")],
        # Строка 3
        [InlineKeyboardButton(text=BTN_PRODUCTS, callback_data="building_products"),
         InlineKeyboardButton(text=BTN_PAWNSHOP, callback_data="building_pawnshop")],
        # Строка 4
        [InlineKeyboardButton(text=BTN_TAVERN, callback_data="building_tavern"),
         InlineKeyboardButton(text=BTN_ENTERTAINMENT, callback_data="building_entertainment")],
        # Строка 5
        [InlineKeyboardButton(text=BTN_REALESTATE, callback_data="building_realestate"),
         InlineKeyboardButton(text=BTN_VETCLINIC, callback_data="building_vetclinic")],
        # Строка 6
        [InlineKeyboardButton(text=BTN_CONSTRUCTION, callback_data="building_construction"),
         InlineKeyboardButton(text=BTN_HOSPITAL, callback_data="building_hospital")],
        # Строка 7
        [InlineKeyboardButton(text=BTN_QUANTUMHUB, callback_data="building_quantumhub"),
         InlineKeyboardButton(text=BTN_CEMETERY, callback_data="building_cemetery")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def show_town_menu(message: Message):
    """Показать меню города"""
    try:
        text = """
🏘️ **ГОРОД ОСТРОВ RYABOT**

Добро пожаловать в центр цивилизации!
Здесь вы найдете все необходимое для развития своего хозяйства.

🏛️ В ратуше можно зарегистрироваться и купить лицензии
🎓 В академии - нанимать и обучать рабочих
💍 В ломбарде - продавать ценности
🛒 На рынке - покупать товары и животных

Выберите здание:
        """.strip()
        
        await message.answer(text, reply_markup=get_town_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка показа города: {e}")
        await message.answer(ERROR_GENERAL)

# === ОБРАБОТЧИКИ ЗДАНИЙ ===

@router.callback_query(F.data.startswith("building_"))
async def handle_building(callback: CallbackQuery):
    """Обработка зданий"""
    try:
        building = callback.data.split("_")[1]  # building_townhall -> townhall
        user_id = callback.from_user.id
        
        # Проверяем туториал для некоторых зданий
        tutorial_step = await tutorial_service.get_tutorial_step(user_id)
        
        # Обработка конкретных зданий
        if building == "townhall":
            await handle_townhall(callback, tutorial_step)
        elif building == "academy":
            await handle_academy(callback, tutorial_step)
        elif building == "pawnshop":
            await handle_pawnshop(callback, tutorial_step)
        elif building == "tavern":
            await handle_tavern(callback, tutorial_step)
        else:
            # Заглушка для остальных зданий
            await callback.message.edit_text(
                f"{BUILDING_NAMES.get(building, building.title())}\n\n{SECTION_UNDER_DEVELOPMENT}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_town")]
                ])
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка здания {callback.data}: {e}")
        await callback.answer("Ошибка", show_alert=True)

async def handle_townhall(callback: CallbackQuery, tutorial_step):
    """Обработка ратуши"""
    text = """
🏛️ **РАТУША ОСТРОВА**

Официальный центр управления островом.
Строгий мраморный зал с золотым яйцом на постаменте.

👨‍💼 **Услуги:**
• Регистрация граждан (10 рябаксов)
• Лицензия Работодателя LV1 (100 рябаксов)  
• Фермерская лицензия LV1 (200 рябаксов)
• Просмотр статистики острова

Клерк нетерпеливо стучит ручкой...
    """.strip()
    
    # В туториале показываем специальные кнопки
    if tutorial_step.value in ["town_hall_register", "employer_license", "farm_license"]:
        keyboard = []
        if tutorial_step.value == "town_hall_register":
            keyboard.append([InlineKeyboardButton(text="📝 Зарегистрироваться (10 💵)", callback_data="tutorial_register")])
        elif tutorial_step.value == "employer_license":
            keyboard.append([InlineKeyboardButton(text="📜 Лицензия работодателя (100 💵)", callback_data="tutorial_buy_employer_license")])
        elif tutorial_step.value == "farm_license":
            keyboard.append([InlineKeyboardButton(text="🌾 Фермерская лицензия (200 💵)", callback_data="tutorial_buy_farm_license")])
    else:
        keyboard = [
            [InlineKeyboardButton(text="📊 Статистика острова", callback_data="townhall_stats")],
            [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_town")]
        ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

async def handle_academy(callback: CallbackQuery, tutorial_step):
    """Обработка академии"""  
    text = """
🎓 **АКАДЕМИЯ ОСТРОВА**

Центр образования и найма рабочих.
Здесь можно нанимать простых рабочих и обучать их на специалистов.

💼 **Биржа труда:**
• Найм рабочих (30 рябаксов)
• Кулдаун между наймами: 1 час

🎓 **Обучение специалистов:**
• Фермер (животноводство, растениеводство)
• Строитель (возведение зданий)
• Рыбак (морская рыбалка)
• Лесник (добыча древесины)
    """.strip()
    
    keyboard = [
        [InlineKeyboardButton(text=BTN_LABOR_EXCHANGE, callback_data="academy_labor")],
        [InlineKeyboardButton(text=BTN_EXPERT_COURSES, callback_data="academy_courses")],
        [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_town")]
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

async def handle_pawnshop(callback: CallbackQuery, tutorial_step):
    """Обработка ломбарда"""
    text = """
💍 **ЛОМБАРД "ОСКОЛОК И МОНЕТА"**

Тесная лавочка, заставленная тикающими артефактами и куриными перьями.

👴 **Борислав** (владелец):
*"Скупаю золотые осколки, редкие предметы и сокровища!  
Честные цены, быстрый расчет."*

💎 **Принимаем:**
• Золотые осколки
• Редкие артефакты  
• Сокровища с экспедиций
• Ювелирные изделия
    """.strip()
    
    # В туториале - продажа осколка
    if tutorial_step.value == "pawn_shop":
        keyboard = [
            [InlineKeyboardButton(text="💰 Продать осколок за 500 💵", callback_data="tutorial_sell_shard")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(text="💎 Продать предметы", callback_data="pawnshop_sell")],
            [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_town")]
        ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

async def handle_tavern(callback: CallbackQuery, tutorial_step):
    """Обработка таверны"""
    text = """
🍻 **ТАВЕРНА У МОРЯ**

Уютное место у берега с видом на океан.
Здесь собираются местные жители, рыбаки и путешественники.

👨‍🍳 **Бармен:**
*"Добро пожаловать! У нас лучший ром на острове  
и свежие новости от торговцев."*

🍺 **Услуги:**
• Отдых и восстановление энергии
• Слухи и новости острова
• Встречи с другими игроками
• Квесты от местных жителей
    """.strip()
    
    keyboard = [
        [InlineKeyboardButton(text="🍻 Купить ром (+10 энергии)", callback_data="tavern_rum")],
        [InlineKeyboardButton(text="📰 Послушать новости", callback_data="tavern_news")],
        [InlineKeyboardButton(text=BTN_BACK, callback_data="back_to_town")]
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

# === НАВИГАЦИЯ ===

@router.callback_query(F.data == "back_to_town")
async def back_to_town(callback: CallbackQuery):
    """Возврат в город"""
    try:
        text = """
🏘️ **ГОРОД ОСТРОВ RYABOT**

Выберите здание:
        """.strip()
        
        await callback.message.edit_text(
            text,
            reply_markup=get_town_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка возврата в город: {e}")
        await callback.answer("Ошибка", show_alert=True)

# Названия зданий для заглушек
BUILDING_NAMES = {
    "market": "🛒 Рынок",
    "ryabank": "🏦 РяБанк", 
    "products": "📦 Товары",
    "entertainment": "🎪 Развлечения",
    "realestate": "🖼️ Недвижка",
    "vetclinic": "🏥 Ветклиника",
    "construction": "🏗️ Строй-Сам",
    "hospital": "🏥 Больница",
    "quantumhub": "⚛️ Квантум-Хаб",
    "cemetery": "⚰️ Кладбище"
}