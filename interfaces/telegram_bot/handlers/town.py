# interfaces/telegram_bot/handlers/town.py
"""
Handler для города и академии
"""

import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

# Core imports
from core.use_cases.user.create_user import GetUserProfileUseCase, UpdateUserResourcesUseCase
from adapters.database.supabase.client import get_supabase_client
from adapters.database.supabase.repositories.user_repository import SupabaseUserRepository

# Interface imports
from ..localization.texts import get_text, t
from ..keyboards.main_menu import get_academy_menu, get_labor_exchange_menu, get_expert_courses_menu, get_back_keyboard
from ..keyboards.town_menu import get_town_menu
from ..states import MenuState, AcademyState

router = Router()
logger = logging.getLogger(__name__)


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

async def get_user_use_cases():
    """Фабрика Use Cases"""
    client = await get_supabase_client()
    user_repo = SupabaseUserRepository(client)

    return {
        'get_profile': GetUserProfileUseCase(user_repo),
        'update_resources': UpdateUserResourcesUseCase(user_repo)
    }


async def get_user_lang(user_id: int) -> str:
    """Получить язык пользователя"""
    try:
        client = await get_supabase_client()
        user_data = await client.execute_query(
            table="users",
            operation="select",
            columns=["language"],
            filters={"user_id": user_id},
            single=True
        )
        return user_data['language'] if user_data else 'ru'
    except:
        return 'ru'


async def get_specialists_count(user_id: int) -> dict:
    """Получить количество специалистов"""
    try:
        client = await get_supabase_client()

        # Получаем всех специалистов пользователя
        specialists = await client.execute_query(
            table="specialists",
            operation="select",
            columns=["specialist_type"],
            filters={"user_id": user_id}
        )

        # Подсчитываем по типам
        counts = {}
        for spec in specialists:
            spec_type = spec['specialist_type']
            counts[spec_type] = counts.get(spec_type, 0) + 1

        return counts

    except Exception as e:
        logger.error(f"Ошибка получения специалистов для {user_id}: {e}")
        return {}


async def get_workers_count(user_id: int) -> int:
    """Получить количество простых рабочих"""
    try:
        client = await get_supabase_client()

        workers = await client.execute_query(
            table="specialists",
            operation="select",
            columns=["id"],
            filters={"user_id": user_id, "specialist_type": "worker"}
        )

        return len(workers) if workers else 0

    except Exception as e:
        logger.error(f"Ошибка получения рабочих для {user_id}: {e}")
        return 0


async def can_hire_worker(user_id: int) -> tuple[bool, str, int]:
    """
    Проверка возможности найма рабочего
    Returns: (можно_ли, причина, оставшееся_время_в_секундах)
    """
    try:
        client = await get_supabase_client()

        # Проверяем последний найм
        last_hire = await client.execute_query(
            table="specialists",
            operation="select",
            columns=["hired_at"],
            filters={"user_id": user_id},
            limit=1
        )

        if last_hire:
            last_hire_time = datetime.fromisoformat(last_hire[0]['hired_at'])
            cooldown_end = last_hire_time + timedelta(hours=1)  # 1 час кулдаун

            if datetime.now() < cooldown_end:
                remaining = int((cooldown_end - datetime.now()).total_seconds())
                return False, "cooldown", remaining

        # Проверяем лимит (нужны дома)
        workers_count = await get_workers_count(user_id)
        specialists_count = await get_specialists_count(user_id)
        total_workers = workers_count + sum(specialists_count.values())

        # Получаем количество домов
        houses = await client.execute_query(
            table="buildings",
            operation="select",
            columns=["id"],
            filters={"user_id": user_id, "building_type": "house"}
        )

        house_count = len(houses) if houses else 0
        max_workers = 3 + (house_count * 3)  # 3 базовых + 3 на дом

        if total_workers >= max_workers:
            return False, "limit_reached", 0

        return True, "ready", 0

    except Exception as e:
        logger.error(f"Ошибка проверки найма для {user_id}: {e}")
        return False, "unknown", 0


async def hire_worker(user_id: int) -> tuple[bool, str]:
    """
    Нанять рабочего
    Returns: (успех, сообщение)
    """
    try:
        # Проверяем возможность найма
        can_hire, reason, remaining = await can_hire_worker(user_id)

        if not can_hire:
            if reason == "cooldown":
                hours = remaining // 3600
                minutes = (remaining // 60) % 60
                return False, f"⏰ Кулдаун: {hours}ч {minutes}м"
            elif reason == "limit_reached":
                return False, "🏠 Нужно построить больше домов"
            else:
                return False, "❌ Неизвестная ошибка"

        # Проверяем деньги
        use_cases = await get_user_use_cases()
        profile = await use_cases['get_profile'].execute(user_id)

        # Стоимость найма (растет с количеством рабочих)
        current_workers = await get_workers_count(user_id)
        cost = 30 + (5 * current_workers)  # 30, 35, 40, 45...

        if profile['ryabucks'] < cost:
            return False, f"💰 Недостаточно рябаксов! Нужно {cost}"

        # Списываем деньги
        await use_cases['update_resources'].execute(user_id, {
            "ryabucks": profile['ryabucks'] - cost
        })

        # Добавляем рабочего в БД
        client = await get_supabase_client()
        await client.execute_query(
            table="specialists",
            operation="insert",
            data={
                "user_id": user_id,
                "specialist_type": "worker",
                "level": 1,
                "experience": 0,
                "hired_at": datetime.now().isoformat()
            }
        )

        # Обновляем статистику
        user_repo = SupabaseUserRepository(client)
        await user_repo.increment_stat(user_id, "specialists_hired")
        await user_repo.increment_stat(user_id, "laborers_hired")

        new_count = current_workers + 1
        return True, f"🎉 Рабочий успешно нанят! Теперь у вас {new_count} рабочих."

    except Exception as e:
        logger.error(f"Ошибка найма рабочего для {user_id}: {e}")
        return False, "❌ Ошибка найма рабочего"


# === ГОРОД ===

@router.message(F.text.in_(["🏘️ Город", "🏘️ Town"]))
async def town_menu(message: Message, state: FSMContext):
    """Меню города"""
    try:
        user_id = message.from_user.id
        lang = await get_user_lang(user_id)

        town_text = t("town_text", lang)
        await message.answer(
            town_text,
            reply_markup=get_town_menu(lang)
        )
        await state.set_state(MenuState.IN_TOWN)

    except Exception as e:
        logger.error(f"❌ Ошибка меню города: {e}")
        await message.answer(t("error_general", "ru"))


# === АКАДЕМИЯ ===

@router.callback_query(F.data == "academy")
async def academy_main(callback: CallbackQuery, state: FSMContext):
    """Главное меню академии"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        # Получаем статистику
        workers_count = await get_workers_count(user_id)
        specialists_count = await get_specialists_count(user_id)

        # TODO: Получить количество обучающихся (пока 0)
        training_count = 0

        total_specialists = sum(specialists_count.values())

        academy_text = t("academy_welcome", lang).format(
            laborers=workers_count,
            training=training_count,
            specialists=total_specialists
        )

        await callback.message.edit_text(
            academy_text,
            reply_markup=get_academy_menu(lang)
        )
        await state.set_state(AcademyState.MAIN_MENU)
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка академии для {callback.from_user.id}: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


@router.callback_query(F.data == "academy_labor_exchange")
async def labor_exchange(callback: CallbackQuery, state: FSMContext):
    """Биржа труда"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        # Получаем статистику
        workers_count = await get_workers_count(user_id)
        specialists_count = await get_specialists_count(user_id)
        total_workers = workers_count + sum(specialists_count.values())

        # Проверяем возможность найма
        can_hire, reason, remaining = await can_hire_worker(user_id)

        # Формируем статус найма
        if can_hire:
            cost = 30 + (5 * workers_count)
            status = t("hire_status_ready", lang).format(cost=cost)
        elif reason == "cooldown":
            hours = remaining // 3600
            minutes = (remaining // 60) % 60
            status = t("hire_status_cooldown", lang).format(hours=hours, minutes=minutes)
        elif reason == "limit_reached":
            status = t("hire_status_limit", lang)
        else:
            status = t("hire_status_unknown", lang)

        exchange_text = t("labor_exchange", lang).format(
            laborers=workers_count,
            total_workers=total_workers,
            status=status
        )

        await callback.message.edit_text(
            exchange_text,
            reply_markup=get_labor_exchange_menu(can_hire, total_workers, lang)
        )
        await state.set_state(AcademyState.LABOR_EXCHANGE)
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка биржи труда: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


@router.callback_query(F.data == "hire_worker")
async def hire_worker_callback(callback: CallbackQuery):
    """Найм рабочего"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        success, message = await hire_worker(user_id)

        await callback.answer(message, show_alert=True)

        if success:
            # Обновляем меню биржи труда
            await labor_exchange(callback, None)  # Перерисовываем меню

    except Exception as e:
        logger.error(f"❌ Ошибка найма рабочего: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


@router.callback_query(F.data == "academy_expert_courses")
async def expert_courses(callback: CallbackQuery, state: FSMContext):
    """Курсы экспертов"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        workers_count = await get_workers_count(user_id)

        # TODO: Получить слоты обучения (пока 2/2)
        slots_used = 0
        slots_total = 2

        courses_text = t("expert_courses", lang).format(
            laborers=workers_count,
            slots_used=slots_used,
            slots_total=slots_total
        )

        await callback.message.edit_text(
            courses_text,
            reply_markup=get_expert_courses_menu(lang)
        )
        await state.set_state(AcademyState.EXPERT_COURSES)
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка курсов экспертов: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


@router.callback_query(F.data == "academy_training_class")
async def training_class(callback: CallbackQuery, state: FSMContext):
    """Класс обучения"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        # TODO: Получить активные обучения (пока пусто)
        active_trainings = []

        if not active_trainings:
            class_text = t("training_class_empty", lang)
        else:
            # Формируем список обучающихся
            training_list = "\n".join([f"{i + 1}. {training}" for i, training in enumerate(active_trainings)])

            class_text = t("training_class_active", lang).format(
                slots_used=len(active_trainings),
                slots_total=2,
                training_list=training_list
            )

        await callback.message.edit_text(
            class_text,
            reply_markup=get_back_keyboard("academy", lang)
        )
        await state.set_state(AcademyState.TRAINING_CLASS)
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка класса обучения: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


# === ОБУЧЕНИЕ СПЕЦИАЛИСТОВ ===

@router.callback_query(F.data.startswith("train_"))
async def start_training(callback: CallbackQuery):
    """Начать обучение специалиста"""
    try:
        profession = callback.data.split("_")[1]
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        # Проверяем наличие свободных рабочих
        workers_count = await get_workers_count(user_id)

        if workers_count == 0:
            await callback.answer(t("training_no_workers", lang), show_alert=True)
            return

        # TODO: Проверить слоты обучения

        # TODO: Реализовать систему обучения
        # Пока просто заглушка

        profession_names = {
            "farmer": "Фермера" if lang == "ru" else "Farmer",
            "builder": "Строителя" if lang == "ru" else "Builder",
            "fisherman": "Рыбака" if lang == "ru" else "Fisherman",
            "forester": "Лесника" if lang == "ru" else "Forester"
        }

        profession_name = profession_names.get(profession, profession)

        await callback.answer(
            f"🎓 Обучение на {profession_name} начато! (В разработке)",
            show_alert=True
        )

    except Exception as e:
        logger.error(f"❌ Ошибка начала обучения: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


# === НАВИГАЦИЯ ===

@router.callback_query(F.data == "back_to_town")
async def back_to_town(callback: CallbackQuery, state: FSMContext):
    """Возврат в город"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        town_text = t("town_text", lang)
        await callback.message.edit_text(
            town_text,
            reply_markup=get_town_menu(lang)
        )
        await state.set_state(MenuState.IN_TOWN)
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка возврата в город: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)


# === ЗАГЛУШКИ ЗДАНИЙ ===

@router.callback_query(F.data.in_([
    "townhall", "market", "ryabank", "products", "pawnshop",
    "tavern1", "entertainment", "realestate", "vetclinic",
    "construction", "hospital", "quantumhub", "cemetery"
]))
async def building_handler(callback: CallbackQuery):
    """Обработка нажатий на здания (заглушки)"""
    try:
        building = callback.data
        user_id = callback.from_user.id
        lang = await get_user_lang(user_id)

        building_text = t(f"building_{building}", lang)

        await callback.message.edit_text(
            building_text,
            reply_markup=get_back_keyboard("back_to_town", lang)
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка здания {callback.data}: {e}")
        await callback.answer(t("error_general", "ru"), show_alert=True)