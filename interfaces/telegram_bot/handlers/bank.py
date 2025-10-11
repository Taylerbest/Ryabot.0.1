"""
Хендлер Рябанка - игровой банк с DEX механикой
"""
import logging
import decimal
from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from config.texts import *
from services.bank_service import bank_service
from interfaces.telegram_bot.states import BankState
from adapters.database.supabase.client import get_supabase_client
from aiogram.types import LabeledPrice


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
    """Показать меню рябанка с экономической информацией"""
    try:
        logger.info("📊 Показываем меню банка - show_bank_menu")

        # Получаем пулы банка
        pools = await bank_service.get_bank_pools()
        logger.info(f"RBTC={pools['rbtc_pool']}, Рябаксы={pools['ryabucks_pool']}, Курс={pools['current_rate']:.2f}")

        # Рассчитываем мультипликатор экономики
        initial_bank = 1_050_000_000  # Начальная сумма
        current_bank = float(pools['total_bank_ryabucks'])
        economy_multiplier = max(0.2, min(5.0, current_bank / initial_bank))

        # Определяем статус экономики
        if economy_multiplier >= 3.0:
            economy_status = "🔥 Гиперинфляция"
        elif economy_multiplier >= 2.0:
            economy_status = "📈 Высокая инфляция"
        elif economy_multiplier >= 1.5:
            economy_status = "📊 Умеренная инфляция"
        elif economy_multiplier >= 0.8:
            economy_status = "⚖️ Стабильность"
        elif economy_multiplier >= 0.5:
            economy_status = "📉 Дефляция"
        else:
            economy_status = "❄️ Глубокая дефляция"

        # Форматируем текст меню
        bank_text = f"""〰️〰️〰️ 🏦 РЯБАНК 〰️〰️〰️

«14 банков объединились в один — великий центр финансовой мощи острова. Здесь курсы валют устанавливаются спросом и предложением, а каждая сделка меняет экономику».

💱 **Текущий курс:**
1 RBTC = {pools['current_rate']:.2f} рябаксов

📊 **Пулы банка:**
• RBTC: {float(pools['rbtc_pool']):.0f}
• Рябаксы: {int(pools['ryabucks_pool']):,}

💰 **Экономика острова:**
• Общий банк: {int(current_bank):,} рябаксов
• Мультипликатор: x{economy_multiplier:.2f}
• Статус: {economy_status}

🥚 Золотых яиц вложено: {pools['total_invested_golden_eggs']}"""

        logger.info(f"Текст меню банка (Telegram безопасный): {len(bank_text)} символов")

        await callback.message.edit_text(bank_text, reply_markup=get_bank_keyboard())
        logger.info("✅ Меню банка отправлено")
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка показа меню банка: {e}", exc_info=True)
        await callback.answer("Техническая ошибка", show_alert=True)


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

        # Кнопка возврата в банк
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏦 Вернуться в банк", callback_data="town_ryabank")]
        ])

        await callback.message.edit_text(
            message_text,
            parse_mode=None,
            reply_markup=keyboard
        )

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

        # Очистка и валидация ввода
        try:
            text = message.text.strip().replace(',', '.').replace(' ', '')
            if not text:
                await message.answer("❌ Введите сумму")
                return

            amount = Decimal(text)

            if amount <= 0:
                await message.answer("❌ Сумма должна быть больше 0")
                return

            if amount > user_rbtc:
                await message.answer(f"❌ У вас есть только: {user_rbtc:.4f} 💠 RBTC")
                return

        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            logger.error(f"Ошибка парсинга суммы продажи: {e}, текст: '{message.text}'")
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

        # Кнопка возврата в банк
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏦 Вернуться в банк", callback_data="town_ryabank")]
        ])

        await callback.message.edit_text(
            message_text,
            parse_mode=None,
            reply_markup=keyboard
        )

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
    """Покупка рябаксов за Telegram Stars - МЕНЮ ВЫБОРА"""
    try:
        pools = await bank_service.get_bank_pools()
        current_rate = float(pools['current_rate'])

        from config.global_pools import STARS_PACKAGES

        RBTC_EQUIV = 14.3

        base_ryabucks = int(RBTC_EQUIV * current_rate)

        stars_text = f"""⭐ Покупка рябаксов за Telegram Stars

📊 Текущий курс: 1 💠 = {current_rate:.2f} 💵

За 100 ⭐ получите: {base_ryabucks:,} 💵 рябаксов
(эквивалент {RBTC_EQUIV} 💠 RBTC)

Выберите пакет:"""

        keyboard = []
        for package in STARS_PACKAGES[:4]:
            stars = package['stars']
            bonus = package['bonus']
            ryabucks = int((stars / 100.0) * RBTC_EQUIV * current_rate * (1.0 + bonus / 100.0))

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


@router.callback_query(F.data.startswith("buy_stars_"))
async def process_buy_stars(callback: CallbackQuery):
    """Обработка покупки рябаксов за Stars - СОЗДАНИЕ ИНВОЙСА"""
    try:
        stars = int(callback.data.split("_")[2])

        logger.info(f"💫 Покупка за {stars} ⭐ от user {callback.from_user.id}")

        pools = await bank_service.get_bank_pools()
        current_rate = float(pools['current_rate'])

        from config.global_pools import STARS_PACKAGES

        RBTC_EQUIV = 14.3

        bonus_percent = 0
        for package in STARS_PACKAGES:
            if package['stars'] == stars:
                bonus_percent = package['bonus']
                break

        base_amount = int((stars / 100.0) * RBTC_EQUIV * current_rate)
        bonus_amount = int(base_amount * bonus_percent / 100.0)
        total_ryabucks = base_amount + bonus_amount

        bonus_text = f" +{bonus_percent}% бонус!" if bonus_percent > 0 else ""

        prices = [LabeledPrice(label=f"{stars} Stars", amount=stars)]

        await callback.bot.send_invoice(
            chat_id=callback.message.chat.id,
            title="💵 Покупка рябаксов",
            description=f"Получите {total_ryabucks:,} рябаксов{bonus_text}",
            payload=f"stars_{stars}_{callback.from_user.id}",
            provider_token="",
            currency="XTR",
            prices=prices
        )

        await callback.answer("Инвойс создан!")

    except Exception as e:
        logger.error(f"❌ Ошибка создания инвойса: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query):
    """Подтверждение перед оплатой"""
    try:
        logger.info(f"✅ Pre-checkout от {pre_checkout_query.from_user.id}")
        await pre_checkout_query.answer(ok=True)
    except Exception as e:
        logger.error(f"❌ Ошибка pre-checkout: {e}")
        await pre_checkout_query.answer(ok=False, error_message="Ошибка")


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """Успешный платёж"""
    try:
        payment = message.successful_payment
        logger.info(f"💰 Платёж: {payment.total_amount} {payment.currency}")

        parts = payment.invoice_payload.split("_")
        stars = int(parts[1])
        user_id = int(parts[2])

        success, msg, amount = await bank_service.buy_ryabucks_with_stars(user_id, stars)

        if success:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏦 Вернуться в банк", callback_data="town_ryabank")]
            ])
            await message.answer(f"✅ {msg}", parse_mode=None, reply_markup=keyboard)
        else:
            await message.answer(f"❌ {msg}", parse_mode=None)

    except Exception as e:
        logger.error(f"❌ Ошибка платежа: {e}")
        await message.answer("Ошибка зачисления")



# TODO: Реализовать обработчики для:
# - bank_invest_golden_egg (инвестиции золотых яиц)
# - bank_withdraw_rbtc (вывод RBTC)
# - bank_send_rbtc (отправка RBTC другим игрокам)
# - buy_stars_* (обработка оплаты через Telegram Stars)

logger.info("Bank handlers loaded successfully")
