"""
Хендлер Рябанка - игровой банк с DEX механикой
"""
import logging
from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from config.texts import *
from services.bank_service import bank_service
from interfaces.telegram_bot.states import BankState
from adapters.database.supabase.client import get_supabase_client

router = Router()
logger = logging.getLogger(__name__)


def get_bank_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура главного меню банка"""
    keyboard = [
        [
            InlineKeyboardButton(text="🟢 Купить [💵]", callback_data="bank_buy_ryabucks"),
            InlineKeyboardButton(text="🟢 Купить [💠]", callback_data="bank_buy_rbtc")
        ],
        [
            InlineKeyboardButton(text="💸 Вложить [⚜️]", callback_data="bank_invest_golden_egg"),
            InlineKeyboardButton(text="🔴 Продать [💠]", callback_data="bank_sell_rbtc")
        ],
        [
            InlineKeyboardButton(text="📤 Вывести [💠]", callback_data="bank_withdraw_rbtc"),
            InlineKeyboardButton(text="📨 Послать [💠]", callback_data="bank_send_rbtc")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_town")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data == "town_ryabank")
async def show_bank_menu(callback: CallbackQuery):
    """Показать главное меню Рябанка"""
    try:
        # Получить состояние пулов
        pools = await bank_service.get_bank_pools()

        bank_text = f"""〰️〰️ 🏦 ₽ЯБАНК ℹ️ 🔋14  〰️〰️

Крепость богатства, где золотые яйца 
блестят в свете хрустальных фонарей.

Воздух здесь наполнен звоном 
монет и шелестом страниц бухгалтерских книг. 
Полированные мраморные полы отражают сияние 
золотых сводов, а серьёзные на вид 
клерки в жилетах подсчитывают состояния 
за позолоченными железными стойками.

💠 Банковский Пул  
├ Цена 1 [💠]: {pools['current_rate']:.2f} [💵]
└ Total: {pools['rbtc_pool']:.0f} RBTC  

⚜️ Инвестировано: {pools['total_invested_golden_eggs']} золотых яиц"""

        await callback.message.edit_text(
            bank_text,
            reply_markup=get_bank_keyboard()
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка показа меню банка: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


# ═══════════════════════════════════════════════════════════════════════
# ПОКУПКА RBTC ЗА РЯБАКСЫ
# ═══════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "bank_buy_rbtc")
async def buy_rbtc_start(callback: CallbackQuery, state: FSMContext):
    """Начать покупку RBTC"""
    try:
        user_id = callback.from_user.id

        # Получить баланс пользователя
        client = await get_supabase_client()
        user = await client.execute_query(
            table="users",
            operation="select",
            columns=["ryabucks", "rbtc"],
            filters={"user_id": user_id},
            single=True
        )

        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        user_ryabucks = user.get('ryabucks', 0)
        user_rbtc = user.get('rbtc', 0)

        # Получить текущий курс
        pools = await bank_service.get_bank_pools()
        max_rbtc, estimated_cost = await bank_service.calculate_max_buyable_rbtc(user_ryabucks)

        buy_text = f"""🤖 Сколько [ 💠 RBTC ] вы хотите купить?

💰 Ваш баланс:
├ Рябаксы: {user_ryabucks:,} 💵
└ RBTC: {user_rbtc:.4f} 💠

📊 Текущий курс: 1 💠 = {pools['current_rate']:.2f} 💵
📈 Доступно: {max_rbtc:.4f} 💠 RBTC

Введите количество RBTC:"""

        keyboard = [
            [InlineKeyboardButton(text="↩️ Отмена", callback_data="town_ryabank")]
        ]

        await callback.message.edit_text(
            buy_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

        await state.set_state(BankState.BUY_RBTC_AMOUNT)
        await state.update_data(
            max_rbtc=float(max_rbtc),
            user_ryabucks=user_ryabucks,
            current_rate=float(pools['current_rate'])
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка начала покупки RBTC: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.message(BankState.BUY_RBTC_AMOUNT)
async def process_buy_rbtc_amount(message: Message, state: FSMContext):
    """Обработать ввод суммы RBTC для покупки"""
    try:
        data = await state.get_data()
        max_rbtc = data.get('max_rbtc', 0)

        # Очистка и валидация ввода
        import decimal
        try:
            text = message.text.strip().replace(',', '.').replace(' ', '')
            if not text:
                await message.answer("❌ Введите сумму")
                return

            amount = Decimal(text)

            if amount <= 0:
                await message.answer("❌ Сумма должна быть больше 0")
                return

            if amount > max_rbtc:
                await message.answer(f"❌ Максимум доступно: {max_rbtc:.4f} 💠 RBTC")
                return

        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            logger.error(f"Ошибка парсинга суммы RBTC: {e}, текст: '{message.text}'")
            await message.answer("❌ Введите корректную сумму (например: 10.5)")
            return

        # Рассчитать реальную стоимость по AMM
        pools = await bank_service.get_bank_pools()
        from config.global_pools import calculate_buy_rbtc_cost

        try:
            cost = calculate_buy_rbtc_cost(
                amount,
                pools['rbtc_pool'],
                pools['ryabucks_pool']
            )
        except Exception as e:
            logger.error(f"Ошибка расчёта стоимости: {e}")
            await message.answer("❌ Ошибка расчёта стоимости")
            return

        avg_rate = cost / float(amount)

        confirm_text = f"""💰 Подтверждение покупки

Покупаете: {amount:.4f} 💠 RBTC
Стоимость: {cost:,} 💵 рябаксов
Средний курс: 1 💠 = {avg_rate:.2f} 💵

⚠️ Курс меняется при покупке (DEX механика)

Подтвердить покупку?"""

        keyboard = [
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_buy_rbtc"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="town_ryabank")
            ]
        ]

        await message.answer(
            confirm_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

        await state.update_data(amount=float(amount), cost=cost)
        await state.set_state(BankState.BUY_RBTC_CONFIRM)

    except Exception as e:
        logger.error(f"Ошибка обработки суммы покупки RBTC: {e}")
        await message.answer("❌ Произошла ошибка")


@router.callback_query(F.data == "confirm_buy_rbtc")
async def confirm_buy_rbtc(callback: CallbackQuery, state: FSMContext):
    """Подтвердить покупку RBTC"""
    try:
        data = await state.get_data()
        amount = Decimal(str(data.get('amount', 0)))
        user_id = callback.from_user.id

        success, message_text = await bank_service.buy_rbtc(user_id, amount)

        if success:
            await callback.message.edit_text(f"✅ {message_text}")
        else:
            await callback.message.edit_text(f"❌ {message_text}")

        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка подтверждения покупки RBTC: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


# ═══════════════════════════════════════════════════════════════════════
# ПРОДАЖА RBTC ЗА РЯБАКСЫ
# ═══════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "bank_sell_rbtc")
async def sell_rbtc_start(callback: CallbackQuery, state: FSMContext):
    """Начать продажу RBTC"""
    try:
        user_id = callback.from_user.id

        # Получить баланс пользователя
        client = await get_supabase_client()
        user = await client.execute_query(
            table="users",
            operation="select",
            columns=["rbtc", "ryabucks"],
            filters={"user_id": user_id},
            single=True
        )

        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        user_rbtc = Decimal(str(user.get('rbtc', 0)))
        user_ryabucks = user.get('ryabucks', 0)

        pools = await bank_service.get_bank_pools()

        sell_text = f"""🤖 Сколько [ 💠 RBTC ] вы хотите продать?

💰 Ваш баланс:
├ RBTC: {user_rbtc:.4f} 💠
└ Рябаксы: {user_ryabucks:,} 💵

📊 Текущий курс: 1 💠 = {pools['current_rate']:.2f} 💵

Введите количество RBTC:"""

        keyboard = [
            [InlineKeyboardButton(text="↩️ Отмена", callback_data="town_ryabank")]
        ]

        await callback.message.edit_text(
            sell_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

        await state.set_state(BankState.SELL_RBTC_AMOUNT)
        await state.update_data(user_rbtc=float(user_rbtc))
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка начала продажи RBTC: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.message(BankState.SELL_RBTC_AMOUNT)
async def process_sell_rbtc_amount(message: Message, state: FSMContext):
    """Обработать ввод суммы RBTC для продажи"""
    try:
        data = await state.get_data()
        user_rbtc = data.get('user_rbtc', 0)

        try:
            try:
                text = message.text.strip().replace(',', '.').replace(' ', '')
                if not text:
                    await message.answer("❌ Введите сумму")
                    return
                amount = Decimal(text)
            except (ValueError, TypeError, decimal.InvalidOperation):
                await message.answer("❌ Введите корректную сумму (например: 10.5)")
                return

            if amount <= 0:
                await message.answer("❌ Сумма должна быть больше 0")
                return

            if amount > user_rbtc:
                await message.answer(f"❌ У вас есть только: {user_rbtc:.4f} 💠 RBTC")
                return

        except (ValueError, TypeError):
            await message.answer("❌ Введите корректную сумму (например: 10.5)")
            return

        # Рассчитать награду по AMM
        pools = await bank_service.get_bank_pools()
        from config.global_pools import calculate_sell_rbtc_reward

        reward = calculate_sell_rbtc_reward(
            amount,
            pools['rbtc_pool'],
            pools['ryabucks_pool']
        )

        avg_rate = reward / float(amount)

        confirm_text = f"""💰 Подтверждение продажи

Продаете: {amount:.4f} 💠 RBTC
Получите: {reward:,} 💵 рябаксов
Средний курс: 1 💠 = {avg_rate:.2f} 💵

⚠️ Курс меняется при продаже (DEX механика)

Подтвердить продажу?"""

        keyboard = [
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_sell_rbtc"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="town_ryabank")
            ]
        ]

        await message.answer(
            confirm_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

        await state.update_data(amount=float(amount), reward=reward)
        await state.set_state(BankState.SELL_RBTC_CONFIRM)

    except Exception as e:
        logger.error(f"Ошибка обработки суммы продажи RBTC: {e}")
        await message.answer("❌ Произошла ошибка")


@router.callback_query(F.data == "confirm_sell_rbtc")
async def confirm_sell_rbtc(callback: CallbackQuery, state: FSMContext):
    """Подтвердить продажу RBTC"""
    try:
        data = await state.get_data()
        amount = Decimal(str(data.get('amount', 0)))
        user_id = callback.from_user.id

        success, message_text = await bank_service.sell_rbtc(user_id, amount)

        if success:
            await callback.message.edit_text(f"✅ {message_text}")
        else:
            await callback.message.edit_text(f"❌ {message_text}")

        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка подтверждения продажи RBTC: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


# ═══════════════════════════════════════════════════════════════════════
# ПОКУПКА РЯБАКСОВ ЗА TELEGRAM STARS
# ═══════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "bank_buy_ryabucks")
async def buy_ryabucks_stars(callback: CallbackQuery):
    """Покупка рябаксов за Telegram Stars"""
    try:
        pools = await bank_service.get_bank_pools()
        current_rate = pools['current_rate']

        from config.global_pools import STARS_PACKAGES, RBTC_EQUIVALENT

        # Рассчитать сколько рябаксов за базовый пакет
        base_ryabucks = int(RBTC_EQUIVALENT * current_rate)

        stars_text = f"""⭐ Покупка рябаксов за Telegram Stars

📊 Текущий курс: 1 💠 = {current_rate:.2f} 💵

За 100 ⭐ получите: {base_ryabucks:,} 💵 рябаксов
(эквивалент {RBTC_EQUIVALENT} 💠 RBTC)

Выберите пакет:"""

        keyboard = []
        for package in STARS_PACKAGES[:4]:  # Показываем первые 4 пакета
            stars = package['stars']
            bonus = package['bonus']
            ryabucks = int((stars / 100) * RBTC_EQUIVALENT * current_rate * (1 + bonus / 100))

            bonus_text = f" +{bonus}%" if bonus > 0 else ""
            button_text = f"{stars} ⭐ → {ryabucks:,} 💵{bonus_text}"
            keyboard.append([
                InlineKeyboardButton(text=button_text, callback_data=f"buy_stars_{stars}")
            ])

        keyboard.append([
            InlineKeyboardButton(text="↩️ Назад", callback_data="town_ryabank")
        ])

        await callback.message.edit_text(
            stars_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка показа покупки за звезды: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


# TODO: Реализовать обработчики для:
# - bank_invest_golden_egg (инвестиции золотых яиц)
# - bank_withdraw_rbtc (вывод RBTC)
# - bank_send_rbtc (отправка RBTC другим игрокам)
# - buy_stars_* (обработка оплаты через Telegram Stars)

logger.info("Bank handlers loaded successfully")
