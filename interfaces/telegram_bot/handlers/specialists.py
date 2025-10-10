# interfaces/telegram_bot/handlers/specialists.py
"""
Specialist Handler - обработчики для найма и управления специалистами (GDD версия)
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.specialist_service import SpecialistService, SPECIALIST_CONFIG
from services.energy_service import EnergyService
from adapters.database.supabase.repositories.user_repository import SupabaseUserRepository
from adapters.database.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)
router = Router(name="specialists")

# Глобальные сервисы
_specialist_service = None
_energy_service = None

async def get_specialist_service() -> SpecialistService:
    """Получить экземпляр SpecialistService"""
    global _specialist_service
    if not _specialist_service:
        client = await get_supabase_client()
        user_repo = SupabaseUserRepository(client)
        _specialist_service = SpecialistService(user_repo)
    return _specialist_service

async def get_energy_service() -> EnergyService:
    """Получить экземпляр EnergyService"""
    global _energy_service
    if not _energy_service:
        client = await get_supabase_client()
        user_repo = SupabaseUserRepository(client)
        _energy_service = EnergyService(user_repo)
    return _energy_service

@router.callback_query(F.data == "hire_specialists")
async def show_specialists_menu(query: CallbackQuery):
    """Показать меню найма специалистов"""
    try:
        user_id = query.from_user.id
        specialist_service = await get_specialist_service()
        energy_service = await get_energy_service()

        # Получаем информацию об энергии
        energy_info = await energy_service.get_energy_info(user_id)
        current_energy = energy_info["current"] if energy_info else "N/A"

        # Получаем доступных специалистов
        available_specialists = await specialist_service.get_available_specialists(user_id)

        # Получаем текущих специалистов
        current_specialists = await specialist_service.get_user_specialists(user_id)
        current_count = len([s for s in current_specialists if s["status"] != "dead"])

        # Определяем максимум
        max_specialists = await specialist_service._get_max_specialists(user_id)

        # Формируем текст
        text = f"""〰️ 👥 БИРЖА ТРУДА ℹ️ [🔋{current_energy}] 〰️

«Здесь собираются желающие работать за честную плату. От простых рабочих до элитных Q-солдат — каждый найдёт применение своим навыкам».

👷 Специалистов нанято: {current_count}/{max_specialists}

💡 **Для найма требуется:**
• Соответствующая лицензия
• Рябаксы/RBTC и жидкий опыт  
• Достаточно энергии

🏥 **Раненых:** {len([s for s in current_specialists if s['status'] == 'injured'])}
💀 **Погибших:** {len([s for s in current_specialists if s['status'] == 'dead'])}"""

        keyboard = InlineKeyboardBuilder()

        if not available_specialists:
            keyboard.add(InlineKeyboardButton(
                text="🔒 Нет доступных специалистов",
                callback_data="no_specialists"
            ))
        else:
            # Группируем специалистов по 2 в ряд
            for i in range(0, len(available_specialists), 2):
                row = []
                for j in range(2):
                    if i + j < len(available_specialists):
                        spec = available_specialists[i + j]

                        # Показываем цену в рябаксах или RBTC
                        price_display = f"{spec['price_ryabucks']:,}💵"
                        if spec.get('price_rbtc'):
                            price_display += f"/{spec['price_rbtc']:.1f}💠"

                        row.append(InlineKeyboardButton(
                            text=f"{spec['icon']} {price_display}",
                            callback_data=f"hire_spec:{spec['type']}"
                        ))
                keyboard.row(*row)

        # Кнопки управления
        keyboard.row(
            InlineKeyboardButton(text="👥 Мои специалисты", callback_data="my_specialists"),
            InlineKeyboardButton(text="🏥 Госпиталь", callback_data="hospital")
        )

        keyboard.row(
            InlineKeyboardButton(text="🏛️ Академия", callback_data="academy"),
            InlineKeyboardButton(text="↪️ Назад", callback_data="main_menu")
        )

        await query.message.edit_text(text, reply_markup=keyboard.as_markup())
        await query.answer()

    except Exception as e:
        logger.error(f"Ошибка показа меню специалистов для {query.from_user.id}: {e}")
        await query.answer("Техническая ошибка", show_alert=True)

@router.callback_query(F.data.startswith("hire_spec:"))
async def show_specialist_details(query: CallbackQuery):
    """Показать детали специалиста перед наймом"""
    try:
        specialist_type = query.data.split(":")[1]
        user_id = query.from_user.id

        specialist_service = await get_specialist_service()
        available_specialists = await specialist_service.get_available_specialists(user_id)

        # Находим специалиста
        specialist = None
        for spec in available_specialists:
            if spec["type"] == specialist_type:
                specialist = spec
                break

        if not specialist:
            await query.answer("Специалист недоступен", show_alert=True)
            return

        # Формируем текст с деталями
        income_range = f"{specialist['base_income']['min']}-{specialist['base_income']['max']}"
        locations = ", ".join(specialist["work_locations"])

        text = f"""〰️ {specialist['icon']} {specialist['name'].upper()} 〰️

{specialist['description']}

💰 **Стоимость найма:**
• {specialist['price_ryabucks']:,} рябаксов"""

        # Добавляем цену в RBTC если доступна
        if specialist.get('price_rbtc'):
            text += f"\n• {specialist['price_rbtc']:.2f} RBTC"

        text += f"""
• {specialist['price_experience']} жидкого опыта  
• {specialist['energy_cost']} энергии

💼 **Характеристики:**
• Доходность: {income_range} рябаксов/смену
• Локации: {locations}
• Обучение: {specialist['training_time_hours']} часов
• Здоровье: {specialist['max_hp']} HP"""

        # Добавляем боевые характеристики если есть
        if specialist.get("expedition_suitable") and specialist.get("base_stats"):
            stats = specialist["base_stats"]
            text += f"""

⚔️ **Боевые характеристики:**
• Атака: {stats.get('attack', 0)}
• Защита: {stats.get('defense', 0)}
• Эффективность: {stats.get('efficiency', 0)}%
• Лечение: {stats.get('healing_cost', 0)}💵 / {stats.get('healing_time', 0)}ч"""

        keyboard = InlineKeyboardBuilder()

        # Кнопки найма
        keyboard.add(InlineKeyboardButton(
            text=f"✅ Нанять за {specialist['price_ryabucks']:,} 💵",
            callback_data=f"confirm_hire:{specialist_type}:ryabucks"
        ))

        if specialist.get('price_rbtc'):
            keyboard.row(InlineKeyboardButton(
                text=f"✅ Нанять за {specialist['price_rbtc']:.2f} 💠",
                callback_data=f"confirm_hire:{specialist_type}:rbtc"
            ))

        # Кнопка назад
        keyboard.row(InlineKeyboardButton(text="↪️ Назад", callback_data="hire_specialists"))

        await query.message.edit_text(text, reply_markup=keyboard.as_markup())
        await query.answer()

    except Exception as e:
        logger.error(f"Ошибка показа деталей специалиста для {query.from_user.id}: {e}")
        await query.answer("Техническая ошибка", show_alert=True)

@router.callback_query(F.data.startswith("confirm_hire:"))
async def hire_specialist(query: CallbackQuery):
    """Подтвердить найм специалиста"""
    try:
        parts = query.data.split(":")
        specialist_type = parts[1]
        currency = parts[2] if len(parts) > 2 else "ryabucks"
        user_id = query.from_user.id

        specialist_service = await get_specialist_service()

        # Нанимаем специалиста
        success, message = await specialist_service.hire_specialist(user_id, specialist_type, currency)

        if success:
            # Успешный найм
            await query.answer(message, show_alert=True)

            # Возвращаемся к списку специалистов
            await show_specialists_menu(query)
        else:
            # Ошибка найма
            await query.answer(message, show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка найма специалиста для {query.from_user.id}: {e}")
        await query.answer("Техническая ошибка при найме", show_alert=True)

@router.callback_query(F.data == "my_specialists")
async def show_my_specialists(query: CallbackQuery):
    """Показать список нанятых специалистов"""
    try:
        user_id = query.from_user.id
        specialist_service = await get_specialist_service()

        # Получаем специалистов пользователя
        specialists = await specialist_service.get_user_specialists(user_id)

        if not specialists:
            text = """〰️ 👥 МОИ СПЕЦИАЛИСТЫ 〰️

У вас пока нет нанятых специалистов.
Отправляйтесь на биржу труда!"""

            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text="👷 Нанять", callback_data="hire_specialists"))
            keyboard.row(InlineKeyboardButton(text="↪️ Назад", callback_data="hire_specialists"))

        else:
            # Группируем по статусам
            available = [s for s in specialists if s["status"] == "available"]
            working = [s for s in specialists if s["status"] == "working"]
            training = [s for s in specialists if s["status"] == "training"]
            injured = [s for s in specialists if s["status"] == "injured"]
            dead = [s for s in specialists if s["status"] == "dead"]

            text = f"""〰️ 👥 МОИ СПЕЦИАЛИСТЫ ({len(specialists)}) 〰️

Ваши нанятые работники:"""

            if available:
                text += f"\n\n🟢 **Свободны ({len(available)}):**"
                for spec in available[:5]:  # Показываем первых 5
                    hp_bar = "❤️" if spec["current_hp"] == spec["max_hp"] else f"💛{spec['current_hp']}/{spec['max_hp']}"
                    text += f"\n• {spec['icon']} {spec['name']} {hp_bar} (эфф. {spec['efficiency']}%)"

            if working:
                text += f"\n\n🟡 **Работают ({len(working)}):**"
                for spec in working[:3]:
                    text += f"\n• {spec['icon']} {spec['name']}"

            if training:
                text += f"\n\n🎓 **Обучаются ({len(training)}):**" 
                for spec in training[:3]:
                    text += f"\n• {spec['icon']} {spec['name']}"

            if injured:
                text += f"\n\n🏥 **Ранены ({len(injured)}):**"
                for spec in injured[:3]:
                    hp_info = f"{spec['current_hp']}/{spec['max_hp']}❤️ (лечение: {spec['healing_cost']}💵)"
                    text += f"\n• {spec['icon']} {spec['name']} {hp_info}"

            if dead:
                text += f"\n\n💀 **Погибли ({len(dead)}):**"
                for spec in dead[:3]:
                    text += f"\n• 💀 {spec['name']}"

            keyboard = InlineKeyboardBuilder()

            # Кнопки управления
            keyboard.row(
                InlineKeyboardButton(text="📋 Детали", callback_data="specialist_details"),
                InlineKeyboardButton(text="💼 На работу", callback_data="assign_work")
            )

            if injured:
                keyboard.row(
                    InlineKeyboardButton(text="🏥 Лечить всех", callback_data="heal_all"),
                    InlineKeyboardButton(text="🎓 Обучить", callback_data="train_specialist")
                )
            else:
                keyboard.row(
                    InlineKeyboardButton(text="🎓 Обучить", callback_data="train_specialist"),
                    InlineKeyboardButton(text="⚔️ Экспедиция", callback_data="form_squad")
                )

            keyboard.row(InlineKeyboardButton(text="↪️ Назад", callback_data="hire_specialists"))

        await query.message.edit_text(text, reply_markup=keyboard.as_markup())
        await query.answer()

    except Exception as e:
        logger.error(f"Ошибка показа специалистов для {query.from_user.id}: {e}")
        await query.answer("Техническая ошибка", show_alert=True)

@router.callback_query(F.data == "hospital")
async def show_hospital(query: CallbackQuery):
    """Показать госпиталь с ранеными специалистами"""
    try:
        user_id = query.from_user.id
        specialist_service = await get_specialist_service()

        # Получаем раненых специалистов
        all_specialists = await specialist_service.get_user_specialists(user_id)
        injured = [s for s in all_specialists if s["status"] == "injured"]

        if not injured:
            text = """〰️ 🏥 ГОСПИТАЛЬ 〰️

«Чистые палаты и опытные врачи готовы помочь вашим раненым специалистам».

✅ Все ваши специалисты здоровы!
Раненых нет."""

            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text="↪️ Назад", callback_data="hire_specialists"))

        else:
            text = f"""〰️ 🏥 ГОСПИТАЛЬ ({len(injured)}) 〰️

«Чистые палаты и опытные врачи готовы помочь вашим раненым специалистам».

🏥 **Пациенты:**"""

            total_cost = 0
            for spec in injured:
                hp_info = f"{spec['current_hp']}/{spec['max_hp']}❤️"
                heal_cost = spec.get('healing_cost', 50)
                total_cost += heal_cost
                text += f"\n• {spec['icon']} {spec['name']} {hp_info} - {heal_cost}💵"

            text += f"\n\n💰 **Общая стоимость лечения:** {total_cost:,} рябаксов"

            keyboard = InlineKeyboardBuilder()

            # Кнопки лечения
            if len(injured) > 1:
                keyboard.add(InlineKeyboardButton(
                    text=f"🏥 Лечить всех ({total_cost:,}💵)",
                    callback_data="heal_all_confirm"
                ))

            # Индивидуальное лечение (показываем первых 3)
            for spec in injured[:3]:
                heal_cost = spec.get('healing_cost', 50)
                keyboard.row(InlineKeyboardButton(
                    text=f"🩹 {spec['icon']} {heal_cost}💵",
                    callback_data=f"heal_spec:{spec['id']}"
                ))

            keyboard.row(InlineKeyboardButton(text="↪️ Назад", callback_data="hire_specialists"))

        await query.message.edit_text(text, reply_markup=keyboard.as_markup())
        await query.answer()

    except Exception as e:
        logger.error(f"Ошибка показа госпиталя для {query.from_user.id}: {e}")
        await query.answer("Техническая ошибка", show_alert=True)

@router.callback_query(F.data.startswith("heal_spec:"))
async def heal_individual_specialist(query: CallbackQuery):
    """Вылечить конкретного специалиста"""
    try:
        specialist_id = int(query.data.split(":")[1])
        user_id = query.from_user.id

        specialist_service = await get_specialist_service()

        # Лечим специалиста
        success, message = await specialist_service.heal_specialist(user_id, specialist_id)

        if success:
            await query.answer(message, show_alert=True)
            # Обновляем госпиталь
            await show_hospital(query)
        else:
            await query.answer(message, show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка лечения специалиста для {query.from_user.id}: {e}")
        await query.answer("Техническая ошибка при лечении", show_alert=True)

# Заглушки для функций в разработке
@router.callback_query(F.data == "no_specialists")
async def no_specialists_available(query: CallbackQuery):
    await query.answer("🔒 Улучшите лицензии для доступа к специалистам", show_alert=True)

@router.callback_query(F.data == "academy")
async def academy_placeholder(query: CallbackQuery):
    await query.answer("🚧 Академия в разработке", show_alert=True)

@router.callback_query(F.data == "heal_all")
async def heal_all_placeholder(query: CallbackQuery):
    await query.answer("🚧 Массовое лечение в разработке", show_alert=True)

@router.callback_query(F.data == "heal_all_confirm")
async def heal_all_confirm_placeholder(query: CallbackQuery):
    await query.answer("🚧 Массовое лечение в разработке", show_alert=True)

@router.callback_query(F.data == "specialist_details")
async def specialist_details_placeholder(query: CallbackQuery):
    await query.answer("🚧 Детальная информация в разработке", show_alert=True)

@router.callback_query(F.data == "assign_work")
async def assign_work_placeholder(query: CallbackQuery):
    await query.answer("🚧 Система работ в разработке", show_alert=True)

@router.callback_query(F.data == "train_specialist")
async def train_specialist_placeholder(query: CallbackQuery):
    await query.answer("🚧 Обучение в академии в разработке", show_alert=True)

@router.callback_query(F.data == "form_squad")
async def form_squad_placeholder(query: CallbackQuery):
    await query.answer("🚧 Система экспедиций в разработке", show_alert=True)

logger.info("✅ Specialist handler (GDD версия) загружен")