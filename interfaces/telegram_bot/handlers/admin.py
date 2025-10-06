# interfaces/telegram_bot/handlers/admin.py
"""
Админ-панель для Ryabot Island - адаптированная под ваш проект
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config.settings import settings
from adapters.database.supabase.client import get_supabase_client

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Проверка админских прав"""
    try:
        admin_ids = [
            123456789,  # Ваш Telegram ID - ЗАМЕНИТЕ!
            987654321  # Дополнительные админы
        ]

        # Также проверяем переменную окружения
        if hasattr(settings, 'ADMIN_IDS') and settings.ADMIN_IDS:
            admin_ids.extend(settings.ADMIN_IDS)

        return user_id in admin_ids
    except Exception:
        return False


# === БАЗОВЫЕ АДМИН-КОМАНДЫ ===

@router.message(Command("admin_stats"))
async def admin_stats(message: Message):
    """Статистика бота"""
    if not is_admin(message.from_user.id):
        return

    try:
        client = await get_supabase_client()

        # Общая статистика пользователей
        total_users = await client.execute_query(
            table="users",
            operation="count"
        )

        # Новые за сегодня
        from datetime import datetime, timedelta
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        new_today = await client.execute_query(
            table="users",
            operation="count",
            filters={"created_at__gte": today.isoformat()}
        )

        # Онлайн (активны за последние 10 минут)
        online_threshold = (datetime.now() - timedelta(minutes=10)).isoformat()
        online_users = await client.execute_query(
            table="users",
            operation="count",
            filters={"last_active__gte": online_threshold}
        )

        # Статистика по туториалу
        completed_tutorial = await client.execute_query(
            table="users",
            operation="count",
            filters={"tutorial_completed": True}
        )

        # Статистика специалистов
        specialists = await client.execute_query(
            table="specialists",
            operation="count"
        )

        stats_text = f"""
📊 *СТАТИСТИКА RYABOT ISLAND*

👥 *Пользователи:*
• Всего: {total_users or 0}
• Новых сегодня: {new_today or 0}
• Онлайн: {online_users or 0}
• Завершили туториал: {completed_tutorial or 0}

🎮 *Игровая активность:*
• Всего специалистов: {specialists or 0}

🕒 *Время:* {datetime.now().strftime("%H:%M:%S")}
        """.strip()

        await message.answer(stats_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка статистики: {e}")
        await message.answer(f"❌ Ошибка получения статистики: {str(e)}")


@router.message(Command("admin_user"))
async def admin_user(message: Message):
    """Информация о пользователе: /admin_user 123456789"""
    if not is_admin(message.from_user.id):
        return

    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer("Использование: /admin_user <user_id>")
            return

        target_user_id = int(args[1])
        client = await get_supabase_client()

        # Получаем данные пользователя
        user = await client.execute_query(
            table="users",
            operation="select",
            filters={"user_id": target_user_id},
            single=True
        )

        if not user:
            await message.answer(f"❌ Пользователь {target_user_id} не найден")
            return

        # Получаем специалистов
        specialists = await client.execute_query(
            table="specialists",
            operation="select",
            columns=["specialist_type"],
            filters={"user_id": target_user_id}
        )

        specialist_types = {}
        if specialists:
            for s in specialists:
                spec_type = s['specialist_type']
                specialist_types[spec_type] = specialist_types.get(spec_type, 0) + 1

        user_info = f"""
👤 *ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ*

🆔 *ID:* {user['user_id']}
👤 *Имя:* {user.get('username', 'Не указано')}
🌍 *Язык:* {user.get('language', 'ru')}
🆙 *Уровень:* {user.get('level', 1)}

💰 *Ресурсы:*
💵 Рябаксы: {user.get('ryabucks', 0):,}
💠 RBTC: {user.get('rbtc', 0):.4f}
⚡ Энергия: {user.get('energy', 30)}
🧪 Жидкий опыт: {user.get('liquid_experience', 0)}
💎 Золотые осколки: {user.get('golden_shards', 0)}

📋 *Прогресс:*
🎯 Туториал: {user.get('tutorial_step', 'not_started')}
✅ Завершен: {'Да' if user.get('tutorial_completed', False) else 'Нет'}

👥 *Специалисты:* {len(specialists) if specialists else 0}
{chr(10).join([f"• {spec_type}: {count}" for spec_type, count in specialist_types.items()]) if specialist_types else "• Нет специалистов"}

📅 *Регистрация:* {user.get('created_at', 'Неизвестно')[:10]}
🕒 *Последняя активность:* {user.get('last_active', 'Неизвестно')[:16]}
        """.strip()

        await message.answer(user_info, parse_mode="Markdown")

    except ValueError:
        await message.answer("❌ Неверный формат user_id")
    except Exception as e:
        logger.error(f"Ошибка получения пользователя: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("admin_give"))
async def admin_give(message: Message):
    """Выдать ресурсы: /admin_give 123456789 ryabucks 1000"""
    if not is_admin(message.from_user.id):
        return

    try:
        args = message.text.split()
        if len(args) != 4:
            await message.answer(
                "Использование: /admin_give <user_id> <resource> <amount>\n"
                "Ресурсы: ryabucks, rbtc, energy, liquid_experience, golden_shards"
            )
            return

        target_user_id = int(args[1])
        resource = args[2]
        amount = args[3]

        # Конвертируем сумму
        if resource == 'rbtc':
            amount = float(amount)
        else:
            amount = int(amount)

        valid_resources = ['ryabucks', 'rbtc', 'energy', 'liquid_experience', 'golden_shards']
        if resource not in valid_resources:
            await message.answer(f"❌ Неизвестный ресурс. Доступны: {', '.join(valid_resources)}")
            return

        client = await get_supabase_client()

        # Проверяем существование пользователя
        user = await client.execute_query(
            table="users",
            operation="select",
            columns=["user_id", "username"],
            filters={"user_id": target_user_id},
            single=True
        )

        if not user:
            await message.answer(f"❌ Пользователь {target_user_id} не найден")
            return

        # Выдаем ресурс
        if resource == 'energy':
            # Энергия не может быть больше максимума
            await client.execute_query(
                table="users",
                operation="update",
                data={resource: min(amount, 100)},  # Максимум 100 энергии
                filters={"user_id": target_user_id}
            )
        else:
            # Увеличиваем существующее значение
            current_user = await client.execute_query(
                table="users",
                operation="select",
                columns=[resource],
                filters={"user_id": target_user_id},
                single=True
            )

            current_value = current_user.get(resource, 0) if current_user else 0
            new_value = current_value + amount

            await client.execute_query(
                table="users",
                operation="update",
                data={resource: new_value},
                filters={"user_id": target_user_id}
            )

        await message.answer(
            f"✅ Выдано пользователю {user.get('username', target_user_id)}:\n"
            f"💎 {amount} {resource}"
        )

    except ValueError:
        await message.answer("❌ Неверный формат числа")
    except Exception as e:
        logger.error(f"Ошибка выдачи ресурсов: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("admin_reset"))
async def admin_reset(message: Message):
    """Сбросить туториал: /admin_reset 123456789"""
    if not is_admin(message.from_user.id):
        return

    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer("Использование: /admin_reset <user_id>")
            return

        target_user_id = int(args[1])
        client = await get_supabase_client()

        # Сбрасываем туториал
        await client.execute_query(
            table="users",
            operation="update",
            data={
                "tutorial_step": "not_started",
                "tutorial_completed": False,
                "character_preset": 1,
                "ryabucks": 0,
                "golden_shards": 1,
                "has_employer_license": False,
                "has_farm_license": False,
                "has_island_access": False
            },
            filters={"user_id": target_user_id}
        )

        # Удаляем специалистов
        await client.execute_query(
            table="specialists",
            operation="delete",
            filters={"user_id": target_user_id}
        )

        await message.answer(f"✅ Туториал пользователя {target_user_id} сброшен")

    except ValueError:
        await message.answer("❌ Неверный формат user_id")
    except Exception as e:
        logger.error(f"Ошибка сброса: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("admin_energy"))
async def admin_energy(message: Message):
    """Восстановить энергию: /admin_energy 123456789 100"""
    if not is_admin(message.from_user.id):
        return

    try:
        args = message.text.split()
        if len(args) == 2:
            # Полное восстановление
            target_user_id = int(args[1])
            energy_amount = 100
        elif len(args) == 3:
            # Определенное количество
            target_user_id = int(args[1])
            energy_amount = min(int(args[2]), 100)
        else:
            await message.answer("Использование: /admin_energy <user_id> [amount]")
            return

        client = await get_supabase_client()

        await client.execute_query(
            table="users",
            operation="update",
            data={
                "energy": energy_amount,
                "last_active": datetime.now().isoformat()
            },
            filters={"user_id": target_user_id}
        )

        await message.answer(f"✅ Энергия пользователя {target_user_id} восстановлена до {energy_amount}")

    except ValueError:
        await message.answer("❌ Неверный формат")
    except Exception as e:
        logger.error(f"Ошибка восстановления энергии: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("admin_broadcast"))
async def admin_broadcast(message: Message):
    """Рассылка всем: /admin_broadcast Привет всем!"""
    if not is_admin(message.from_user.id):
        return

    try:
        text = message.text.replace("/admin_broadcast ", "")
        if not text.strip():
            await message.answer("Использование: /admin_broadcast <текст сообщения>")
            return

        client = await get_supabase_client()

        # Получаем всех пользователей
        users = await client.execute_query(
            table="users",
            operation="select",
            columns=["user_id"]
        )

        if not users:
            await message.answer("❌ Нет пользователей для рассылки")
            return

        from aiogram import Bot
        from config.settings import settings
        bot = Bot(token=settings.BOT_TOKEN)

        sent_count = 0
        failed_count = 0

        broadcast_text = f"""
📢 *СООБЩЕНИЕ АДМИНИСТРАЦИИ*

{text}
        """.strip()

        for user in users:
            try:
                await bot.send_message(
                    user['user_id'],
                    broadcast_text,
                    parse_mode="Markdown"
                )
                sent_count += 1
            except Exception:
                failed_count += 1

        await bot.session.close()

        await message.answer(
            f"✅ Рассылка завершена!\n"
            f"📤 Отправлено: {sent_count}\n"
            f"❌ Не удалось: {failed_count}"
        )

    except Exception as e:
        logger.error(f"Ошибка рассылки: {e}")
        await message.answer(f"❌ Ошибка рассылки: {str(e)}")


# === ИНФОРМАЦИОННЫЕ КОМАНДЫ ===

@router.message(Command("admin"))
async def admin_help(message: Message):
    """Список админских команд"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    help_text = """
🛠 *АДМИН-ПАНЕЛЬ RYABOT ISLAND*

📊 *Статистика:*
• `/admin_stats` - общая статистика бота

👤 *Управление пользователями:*
• `/admin_user <id>` - информация о пользователе
• `/admin_give <id> <resource> <amount>` - выдать ресурсы
• `/admin_reset <id>` - сбросить туториал
• `/admin_energy <id> [amount]` - восстановить энергию

📢 *Рассылка:*
• `/admin_broadcast <текст>` - рассылка всем игрокам

💡 *Ресурсы для /admin_give:*
ryabucks, rbtc, energy, liquid_experience, golden_shards

📱 *Версия:* Ryabot Island v4.0
    """.strip()

    await message.answer(help_text, parse_mode="Markdown")


logger.info("✅ Admin handler loaded")