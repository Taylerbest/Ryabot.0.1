# interfaces/telegram_bot/handlers/quantum_pass.py
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from services.quantum_pass_service import quantum_pass_service
from interfaces.telegram_bot.states import QuantumPassState

router = Router()
logger = logging.getLogger(__name__)


def get_quantum_pass_keyboard():
    """Клавиатура меню Quantum Pass"""
    keyboard = [
        [
            InlineKeyboardButton(text="🪪 Купить за 35💠 на 1 мес.", callback_data="qpass_buy_1_month")
        ],
        [
            InlineKeyboardButton(text="🪪 Купить за 84💠 на 3 мес.", callback_data="qpass_buy_3_months")
        ],
        [
            InlineKeyboardButton(text="🪪 Купить за 168💠 на 6 мес.", callback_data="qpass_buy_6_months")
        ],
        [
            InlineKeyboardButton(text="🪪 Купить за 294💠 на 1 год", callback_data="qpass_buy_1_year")
        ],
        [
            InlineKeyboardButton(text="💥 ПРЕИМУЩЕСТВА 💥", url="https://telegra.ph/Preimushchestva-Quantum-Pass-10-07")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_town")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data == "quantum_pass")
async def show_quantum_pass_menu(callback: CallbackQuery):
    """Показать меню Quantum Pass"""
    try:
        user_id = callback.from_user.id

        # Получить статистику Q-Pass
        stats = await quantum_pass_service.get_quantum_pass_stats()

        # Получить информацию о Q-Pass пользователя
        user_qpass_info = await quantum_pass_service.get_user_quantum_pass_info(user_id)

        # Форматировать время
        time_left_text = quantum_pass_service.format_time_left(user_qpass_info['time_left'])

        qpass_text = f"""〰️〰️ 🪪 Q-PASS ℹ️ 〰️〰️

📊 Игроки с пропуском: {stats['total_active_qpass_users']}

Созданный из стабилизированных хроно-частиц, этот экспериментальный пропуск локально изменяет пространство-время, одаривая владельца «заёмной» эффективностью из параллельных реальностей. Побочные эффекты могут включать дежавю, кур, несущих кубические яйца, и временных двойников-сотрудников.

⏳ Время действия Q-Pass: {time_left_text}"""

        await callback.message.edit_text(
            qpass_text,
            reply_markup=get_quantum_pass_keyboard()
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка показа меню Quantum Pass: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("qpass_buy_"))
async def buy_quantum_pass_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение покупки Quantum Pass"""
    try:
        user_id = callback.from_user.id
        duration_key = callback.data.replace("qpass_buy_", "")

        # Получить информацию о пользователе
        user_info = await quantum_pass_service.get_user_quantum_pass_info(user_id)
        user_rbtc = user_info['user_rbtc']

        # Получить цену и описание
        prices = quantum_pass_service.PRICES
        price = prices.get(duration_key, 0)

        duration_descriptions = {
            '1_month': '1 месяц',
            '3_months': '3 месяца',
            '6_months': '6 месяцев',
            '1_year': '1 год'
        }

        duration_text = duration_descriptions.get(duration_key, duration_key)

        # Проверить достаточность средств
        if user_rbtc < price:
            await callback.answer(
                f"❌ Недостаточно RBTC!\nНужно: {price} 💠\nЕсть: {user_rbtc:.4f} 💠",
                show_alert=True
            )
            return

        confirm_text = f"""💰 Подтверждение покупки Quantum Pass

📦 Пакет: {duration_text}
💠 Стоимость: {price} RBTC
💳 Ваш баланс: {user_rbtc:.4f} RBTC
💸 Останется: {user_rbtc - price:.4f} RBTC

⚠️ ВНИМАНИЕ: RBTC будут безвозвратно сожжены из оборота!

Подтвердить покупку?"""

        keyboard = [
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"qpass_confirm_{duration_key}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="quantum_pass")
            ]
        ]

        await callback.message.edit_text(
            confirm_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

        await state.set_data({"duration_key": duration_key})
        await state.set_state(QuantumPassState.PURCHASE_CONFIRM)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка подтверждения покупки Q-Pass: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("qpass_confirm_"))
async def confirm_quantum_pass_purchase(callback: CallbackQuery, state: FSMContext):
    """Выполнить покупку Quantum Pass"""
    try:
        user_id = callback.from_user.id
        duration_key = callback.data.replace("qpass_confirm_", "")

        # Выполнить покупку
        success, message = await quantum_pass_service.purchase_quantum_pass(user_id, duration_key)

        if success:
            await callback.message.edit_text(f"✅ {message}")
        else:
            await callback.message.edit_text(f"❌ {message}")

        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка выполнения покупки Q-Pass: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)
        await state.clear()


logger.info("Quantum Pass handlers loaded")
