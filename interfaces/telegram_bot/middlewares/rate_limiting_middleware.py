"""
Rate limiting middleware для защиты от спама и DDoS атак
"""

import asyncio
import time
from typing import Callable, Dict, Any, Awaitable, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery
import logging

logger = logging.getLogger(__name__)


class RateLimitData:
    """Данные для отслеживания rate limiting"""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()
        self.blocked_until: Optional[datetime] = None
        self.total_requests = 0
        self.blocked_requests = 0


class RateLimitingMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты запросов"""

    def __init__(
            self,
            default_rate_limit: int = 10,  # запросов в минуту
            default_window: int = 60,  # секунд
            admin_rate_limit: int = 100,  # для админов
            block_duration: int = 300,  # блокировка на 5 минут
            cleanup_interval: int = 3600  # очистка каждый час
    ):
        self.default_rate_limit = default_rate_limit
        self.default_window = default_window
        self.admin_rate_limit = admin_rate_limit
        self.block_duration = block_duration
        self.cleanup_interval = cleanup_interval

        # Хранилище данных о пользователях
        self.user_data: Dict[int, RateLimitData] = {}

        # Статистика
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'unique_users': 0,
            'last_cleanup': time.time()
        }

        # Админы (можно расширить)
        self.admins = {123456789, 987654321}  # Замените на реальные ID

        logger.info(f"✅ Rate limiting активен: {default_rate_limit} req/{default_window}s")

    def _is_admin(self, user_id: int) -> bool:
        """Проверка админских прав"""
        return user_id in self.admins

    def _get_rate_limit_config(self, user_id: int) -> tuple[int, int]:
        """Получить конфигурацию rate limiting для пользователя"""
        if self._is_admin(user_id):
            return self.admin_rate_limit, self.default_window
        return self.default_rate_limit, self.default_window

    def _cleanup_old_data(self):
        """Очистка старых данных для экономии памяти"""
        current_time = time.time()

        if current_time - self.stats['last_cleanup'] < self.cleanup_interval:
            return

        cutoff_time = datetime.now() - timedelta(seconds=self.default_window * 2)
        users_to_remove = []

        for user_id, data in self.user_data.items():
            # Очищаем старые запросы
            while data.requests and data.requests[0] < cutoff_time:
                data.requests.popleft()

            # Убираем блокировку если время прошло
            if data.blocked_until and datetime.now() > data.blocked_until:
                data.blocked_until = None

            # Если пользователь давно не активен, удаляем его данные
            if (not data.requests and not data.blocked_until and
                    data.total_requests == 0):
                users_to_remove.append(user_id)

        # Удаляем неактивных пользователей
        for user_id in users_to_remove:
            del self.user_data[user_id]

        self.stats['last_cleanup'] = current_time
        self.stats['unique_users'] = len(self.user_data)

        if users_to_remove:
            logger.info(f"🧹 Очищено данных для {len(users_to_remove)} неактивных пользователей")

    def _is_rate_limited(self, user_id: int) -> tuple[bool, Optional[str]]:
        """Проверить, нужно ли ограничить пользователя"""
        current_time = datetime.now()

        # Получаем или создаем данные пользователя
        if user_id not in self.user_data:
            max_requests, window_seconds = self._get_rate_limit_config(user_id)
            self.user_data[user_id] = RateLimitData(max_requests, window_seconds)

        user_data = self.user_data[user_id]

        # Проверяем блокировку
        if user_data.blocked_until and current_time < user_data.blocked_until:
            remaining = int((user_data.blocked_until - current_time).total_seconds())
            return True, f"Вы заблокированы еще на {remaining} секунд"

        # Если блокировка истекла, снимаем ее
        if user_data.blocked_until and current_time >= user_data.blocked_until:
            user_data.blocked_until = None
            logger.info(f"🔓 Пользователь {user_id} разблокирован")

        # Очищаем старые запросы
        cutoff_time = current_time - timedelta(seconds=user_data.window_seconds)
        while user_data.requests and user_data.requests[0] < cutoff_time:
            user_data.requests.popleft()

        # Проверяем лимит
        if len(user_data.requests) >= user_data.max_requests:
            # Блокируем пользователя
            user_data.blocked_until = current_time + timedelta(seconds=self.block_duration)
            user_data.blocked_requests += 1
            self.stats['blocked_requests'] += 1

            logger.warning(
                f"🚫 Пользователь {user_id} заблокирован на {self.block_duration}s "
                f"за превышение лимита {user_data.max_requests}/{user_data.window_seconds}s"
            )

            return True, (
                f"⏰ Превышен лимит запросов!\n\n"
                f"Лимит: {user_data.max_requests} запросов в {user_data.window_seconds} секунд\n"
                f"Блокировка на {self.block_duration // 60} минут"
            )

        return False, None

    def _record_request(self, user_id: int):
        """Записать запрос пользователя"""
        if user_id not in self.user_data:
            max_requests, window_seconds = self._get_rate_limit_config(user_id)
            self.user_data[user_id] = RateLimitData(max_requests, window_seconds)

        user_data = self.user_data[user_id]
        user_data.requests.append(datetime.now())
        user_data.total_requests += 1
        self.stats['total_requests'] += 1

    def _get_user_id(self, event: TelegramObject) -> Optional[int]:
        """Извлечь user_id из события"""
        if hasattr(event, 'from_user') and event.from_user:
            return event.from_user.id
        elif hasattr(event, 'message') and event.message and event.message.from_user:
            return event.message.from_user.id
        return None

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        """Основная логика middleware"""

        # Периодическая очистка
        self._cleanup_old_data()

        # Извлекаем user_id
        user_id = self._get_user_id(event)

        # Если не можем определить пользователя, пропускаем
        if not user_id:
            return await handler(event, data)

        # Проверяем rate limiting
        is_limited, message = self._is_rate_limited(user_id)

        if is_limited:
            # Отправляем сообщение о превышении лимита
            if isinstance(event, Message):
                try:
                    await event.answer(
                        f"🚫 **Rate Limit**\n\n{message}",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки rate limit сообщения: {e}")
            elif isinstance(event, CallbackQuery):
                try:
                    await event.answer(
                        text=f"Rate limit: {message}",
                        show_alert=True
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки rate limit callback: {e}")

            # Не передаем управление дальше
            return None

        # Записываем запрос
        self._record_request(user_id)

        # Передаем управление дальше
        try:
            return await handler(event, data)
        except Exception as e:
            # В случае ошибки обработки, все равно засчитываем запрос
            logger.error(f"Ошибка в handler после rate limiting: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику rate limiting"""
        return {
            **self.stats,
            'active_users': len(self.user_data),
            'blocked_users': sum(
                1 for data in self.user_data.values()
                if data.blocked_until and datetime.now() < data.blocked_until
            ),
            'config': {
                'default_rate_limit': self.default_rate_limit,
                'default_window': self.default_window,
                'admin_rate_limit': self.admin_rate_limit,
                'block_duration': self.block_duration
            }
        }

    def unblock_user(self, user_id: int) -> bool:
        """Разблокировать пользователя вручную (для админов)"""
        if user_id in self.user_data:
            self.user_data[user_id].blocked_until = None
            logger.info(f"🔓 Пользователь {user_id} разблокирован вручную")
            return True
        return False

    def set_custom_limit(self, user_id: int, max_requests: int, window_seconds: int):
        """Установить индивидуальный лимит для пользователя"""
        if user_id not in self.user_data:
            self.user_data[user_id] = RateLimitData(max_requests, window_seconds)
        else:
            self.user_data[user_id].max_requests = max_requests
            self.user_data[user_id].window_seconds = window_seconds

        logger.info(f"⚙️ Установлен лимит {max_requests}/{window_seconds}s для пользователя {user_id}")


# Глобальный экземпляр middleware
rate_limiter = RateLimitingMiddleware(
    default_rate_limit=15,  # 15 запросов в минуту для обычных пользователей
    default_window=60,  # окно в 60 секунд
    admin_rate_limit=100,  # 100 запросов в минуту для админов
    block_duration=300,  # блокировка на 5 минут
    cleanup_interval=1800  # очистка каждые 30 минут
)

logger.info("✅ Rate limiting middleware инициализирован")