# interfaces/telegram_bot/keyboards/main_menu.py
"""
Основные клавиатуры для бота с Reply кнопками
"""

import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from ..localization.texts import t

logger = logging.getLogger(__name__)


def get_start_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    """
    Стартовое меню (вне острова) с Reply кнопками
    """
    try:
        keyboard = [
            [KeyboardButton(text=t("btn_enter_island", lang))],
            [
                KeyboardButton(text=t("btn_settings", lang)),
                KeyboardButton(text=t("btn_support", lang))
            ]
        ]

        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder=t("menu_placeholder", lang),
            selective=False
        )
    except Exception as e:
        logger.error(f"Error creating start menu: {e}")
        # Fallback клавиатура
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🏝 Войти на остров")],
                [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🆘 Поддержка")]
            ],
            resize_keyboard=True
        )


def get_island_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    """
    Меню острова (внутри острова) с Reply кнопками
    """
    try:
        keyboard = [
            [
                KeyboardButton(text=t("btn_farm", lang)),
                KeyboardButton(text=t("btn_town", lang))
            ],
            [
                KeyboardButton(text=t("btn_citizen", lang)),
                KeyboardButton(text=t("btn_work", lang))
            ],
            [
                KeyboardButton(text=t("btn_inventory", lang)),
                KeyboardButton(text=t("btn_friends", lang))
            ],
            [
                KeyboardButton(text=t("btn_leaderboard", lang)),
                KeyboardButton(text=t("btn_other", lang))
            ],
            [
                KeyboardButton(text=t("btn_leave_island", lang))
            ]
        ]

        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder=t("menu_placeholder", lang),
            selective=False
        )
    except Exception as e:
        logger.error(f"Error creating island menu: {e}")
        # Fallback клавиатура
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🐔 Ферма"), KeyboardButton(text="🏘️ Город")],
                [KeyboardButton(text="👤 Житель"), KeyboardButton(text="💼 Работы")],
                [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="👥 Друзья")],
                [KeyboardButton(text="🏆 Рейтинг"), KeyboardButton(text="📋 Ещё")],
                [KeyboardButton(text="🚪 Покинуть остров")]
            ],
            resize_keyboard=True
        )


def get_language_keyboard() -> InlineKeyboardMarkup:
    """
    Inline клавиатура выбора языка (только для первого запуска)
    """
    try:
        keyboard = [
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
        ]

        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    except Exception as e:
        logger.error(f"Error creating language keyboard: {e}")
        # Fallback клавиатура
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
                [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
            ]
        )


def get_tutorial_keyboard(step: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Клавиатура для туториала
    """
    try:
        if step == 0:  # Стартовый экран туториала
            keyboard = [
                [InlineKeyboardButton(text=t("btn_tutorial_start", lang), callback_data="tutorial_start")],
                [InlineKeyboardButton(text=t("btn_tutorial_skip", lang), callback_data="tutorial_skip")]
            ]
        elif 1 <= step <= 4:  # Шаги туториала
            keyboard = [
                [InlineKeyboardButton(text=t("btn_tutorial_next", lang), callback_data=f"tutorial_step_{step + 1}")],
                [InlineKeyboardButton(text=t("btn_tutorial_skip", lang), callback_data="tutorial_skip")]
            ]
        elif step == 5:  # Найм рабочего
            keyboard = [
                [InlineKeyboardButton(text=t("btn_hire_worker", lang), callback_data="tutorial_hire_worker")],
                [InlineKeyboardButton(text=t("btn_tutorial_skip", lang), callback_data="tutorial_skip")]
            ]
        elif step == 6:  # Обучение
            keyboard = [
                [InlineKeyboardButton(text="👩‍🌾 Фермер" if lang == "ru" else "👩‍🌾 Farmer",
                                      callback_data="tutorial_train_farmer")],
                [InlineKeyboardButton(text="🏗️ Строитель" if lang == "ru" else "🏗️ Builder",
                                      callback_data="tutorial_train_builder")],
                [InlineKeyboardButton(text="🎣 Рыбак" if lang == "ru" else "🎣 Fisherman",
                                      callback_data="tutorial_train_fisherman")]
            ]
        else:  # Завершение
            keyboard = [
                [InlineKeyboardButton(text=t("btn_tutorial_complete", lang), callback_data="tutorial_complete")]
            ]

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    except Exception as e:
        logger.error(f"Error creating tutorial keyboard for step {step}: {e}")
        # Fallback клавиатура
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➡️ Далее", callback_data=f"tutorial_step_{step + 1}")]
            ]
        )


def get_academy_menu(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Меню академии
    """
    try:
        keyboard = [
            [InlineKeyboardButton(text=t("btn_labor_exchange", lang), callback_data="academy_labor_exchange")],
            [InlineKeyboardButton(text=t("btn_expert_courses", lang), callback_data="academy_expert_courses")],
            [InlineKeyboardButton(text=t("btn_training_class", lang), callback_data="academy_training_class")],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="back_to_town")]
        ]

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    except Exception as e:
        logger.error(f"Error creating academy menu: {e}")
        # Fallback клавиатура
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💼 Биржа труда", callback_data="academy_labor_exchange")],
                [InlineKeyboardButton(text="🎓 Курсы экспертов", callback_data="academy_expert_courses")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_town")]
            ]
        )


def get_labor_exchange_menu(can_hire: bool, total_workers: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Меню биржи труда
    """
    try:
        keyboard = []

        if can_hire:
            keyboard.append([InlineKeyboardButton(text=t("btn_hire_worker", lang), callback_data="hire_worker")])

        keyboard.extend([
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="academy")]
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    except Exception as e:
        logger.error(f"Error creating labor exchange menu: {e}")
        # Fallback клавиатура
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="academy")]
            ]
        )


def get_expert_courses_menu(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Меню курсов экспертов
    """
    try:
        keyboard = [
            [InlineKeyboardButton(text="👩‍🌾 Фермер" if lang == "ru" else "👩‍🌾 Farmer", callback_data="train_farmer")],
            [InlineKeyboardButton(text="🏗️ Строитель" if lang == "ru" else "🏗️ Builder",
                                  callback_data="train_builder")],
            [InlineKeyboardButton(text="🎣 Рыбак" if lang == "ru" else "🎣 Fisherman", callback_data="train_fisherman")],
            [InlineKeyboardButton(text="🌲 Лесник" if lang == "ru" else "🌲 Forester", callback_data="train_forester")],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="academy")]
        ]

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    except Exception as e:
        logger.error(f"Error creating expert courses menu: {e}")
        # Fallback клавиатура
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👩‍🌾 Фермер", callback_data="train_farmer")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="academy")]
            ]
        )


def get_back_keyboard(callback_data: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Простая клавиатура с кнопкой "Назад"
    """
    try:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t("btn_back", lang), callback_data=callback_data)]
            ]
        )
    except Exception as e:
        logger.error(f"Error creating back keyboard: {e}")
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
            ]
        )