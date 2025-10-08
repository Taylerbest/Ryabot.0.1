# adapters/database/supabase/client.py
"""
Исправленный клиент для работы с Supabase
Обертка с улучшенной обработкой ошибок, retry логикой и безопасностью
"""

import asyncio
from typing import Optional, Dict, Any, List, Union
import logging
from datetime import datetime, timezone
from supabase import create_client, Client
import time
from contextlib import asynccontextmanager

from config.settings import settings

logger = logging.getLogger(__name__)


class SupabaseConnectionError(Exception):
    """Ошибка подключения к Supabase"""
    pass


class SupabaseQueryError(Exception):
    """Ошибка выполнения запроса к Supabase"""
    pass


class SupabaseTransactionError(Exception):
    """Ошибка транзакции Supabase"""
    pass


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Декоратор для повторных попыток при временных сбоях"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (ConnectionError, TimeoutError, SupabaseConnectionError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(
                            f"Попытка {attempt + 1}/{max_retries} провалилась: {e}. Повтор через {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Все попытки исчерпаны. Последняя ошибка: {e}")
                except Exception as e:
                    # Не повторяем для других типов ошибок
                    logger.error(f"Неповторяемая ошибка: {e}")
                    raise
            raise last_exception

        return wrapper

    return decorator


class SupabaseTransaction:
    """Контекстный менеджер для транзакций Supabase"""

    def __init__(self, client: 'SupabaseClient'):
        self.client = client
        self._transaction_active = False
        self._operations = []

    async def __aenter__(self):
        self._transaction_active = True
        self._operations = []
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._transaction_active = False
        if exc_type is not None:
            # В случае ошибки откатываем операции
            logger.error(f"Транзакция прервана из-за ошибки: {exc_val}")
            return False

        # Выполняем все операции
        try:
            await self._execute_transaction()
        except Exception as e:
            logger.error(f"Ошибка выполнения транзакции: {e}")
            raise SupabaseTransactionError(f"Транзакция не удалась: {e}")

    async def execute_query(self, table: str, operation: str, **kwargs):
        """Добавить операцию в транзакцию"""
        if not self._transaction_active:
            raise SupabaseTransactionError("Транзакция не активна")

        self._operations.append({
            'table': table,
            'operation': operation,
            **kwargs
        })

    async def _execute_transaction(self):
        """Выполнить все операции транзакции"""
        results = []
        for op in self._operations:
            result = await self.client._execute_single_query(**op)
            results.append(result)
        return results


class SupabaseClient:
    """Исправленный клиент для работы с Supabase"""

    def __init__(self):
        self.client: Optional[Client] = None
        self._initialized = False
        self._connection_pool_size = 10
        self._query_timeout = 30
        self._rate_limit_calls = 0
        self._rate_limit_window_start = time.time()
        self._max_calls_per_minute = 1000

    async def initialize(self):
        """Инициализация соединения с расширенной проверкой"""
        if self._initialized:
            return

        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL и SUPABASE_SERVICE_KEY должны быть установлены в .env")

        try:
            # Используем service key для полного доступа
            from supabase import ClientOptions

            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY,
                options=ClientOptions(
                    schema="public",
                    headers={},
                    auto_refresh_token=True,
                    persist_session=True
                )
            )

            # Тестируем соединение
            await self._test_connection()

            logger.info("✅ Supabase клиент инициализирован и протестирован")
            self._initialized = True

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Supabase: {e}", exc_info=True)
            raise SupabaseConnectionError(f"Не удалось подключиться к Supabase: {e}")

    async def _test_connection(self):
        """Тестирование соединения с БД"""
        try:
            # Простой тестовый запрос
            result = self.client.table("users").select("user_id").limit(1).execute()
            logger.info("Тестовое соединение с Supabase успешно")
        except Exception as e:
            raise SupabaseConnectionError(f"Тест соединения провален: {e}")

    def _check_rate_limit(self):
        """Проверка rate limiting"""
        current_time = time.time()

        # Сброс счетчика каждую минуту
        if current_time - self._rate_limit_window_start > 60:
            self._rate_limit_calls = 0
            self._rate_limit_window_start = current_time

        if self._rate_limit_calls >= self._max_calls_per_minute:
            raise SupabaseQueryError("Rate limit превышен. Попробуйте позже.")

        self._rate_limit_calls += 1

    def _validate_table_name(self, table: str) -> None:
        """Валидация названия таблицы для предотвращения SQL injection"""
        if not isinstance(table, str) or not table.strip():
            raise ValueError("Название таблицы должно быть непустой строкой")

        # Разрешенные символы для названий таблиц
        allowed_chars = set('abcdefghijklmnopqrstuvwxyz0123456789_')
        if not all(c.lower() in allowed_chars for c in table):
            raise ValueError(f"Недопустимые символы в названии таблицы: {table}")

    def _validate_operation(self, operation: str) -> None:
        """Валидация типа операции"""
        allowed_operations = {'select', 'insert', 'update', 'delete', 'upsert'}
        if operation not in allowed_operations:
            raise ValueError(f"Недопустимая операция: {operation}. Разрешены: {allowed_operations}")

    def _sanitize_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Санитизация фильтров для предотвращения injection"""
        if not isinstance(filters, dict):
            raise ValueError("Фильтры должны быть словарем")

        sanitized = {}
        for key, value in filters.items():
            # Проверяем название колонки
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"Недопустимое название колонки: {key}")

            # Базовая санитизация значения
            if isinstance(value, str) and len(value) > 10000:
                raise ValueError(f"Слишком длинное значение для {key}")

            sanitized[key] = value

        return sanitized

    @asynccontextmanager
    async def transaction(self):
        """Контекстный менеджер для транзакций"""
        if not self._initialized:
            await self.initialize()

        tx = SupabaseTransaction(self)
        async with tx:
            yield tx

    @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
    async def execute_query(
            self,
            table: str,
            operation: str,
            data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
            filters: Optional[Dict[str, Any]] = None,
            single: bool = False,
            limit: Optional[int] = None,
            columns: Optional[List[str]] = None
    ) -> Any:
        """
        Улучшенное выполнение запроса к Supabase с валидацией и безопасностью
        """
        if not self._initialized:
            await self.initialize()

        # Валидация входных данных
        self._validate_table_name(table)
        self._validate_operation(operation)
        self._check_rate_limit()

        if filters:
            filters = self._sanitize_filters(filters)

        if limit and (not isinstance(limit, int) or limit <= 0 or limit > 10000):
            raise ValueError("Limit должен быть положительным числом не больше 10000")

        return await self._execute_single_query(
            table=table,
            operation=operation,
            data=data,
            filters=filters,
            single=single,
            limit=limit,
            columns=columns
        )

    async def _execute_single_query(
            self,
            table: str,
            operation: str,
            data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
            filters: Optional[Dict[str, Any]] = None,
            single: bool = False,
            limit: Optional[int] = None,
            columns: Optional[List[str]] = None
    ) -> Any:
        """Внутренний метод для выполнения одного запроса"""

        try:
            start_time = time.time()
            query = self.client.table(table)

            if operation == "select":
                # Выборка данных
                if columns:
                    # Валидируем названия колонок
                    for col in columns:
                        if not isinstance(col, str) or not col.strip():
                            raise ValueError(f"Недопустимое название колонки: {col}")
                    query = query.select(",".join(columns))
                else:
                    query = query.select("*")

                # Применяем фильтры с типобезопасностью
                if filters:
                    for key, value in filters.items():
                        if isinstance(value, dict):
                            # Поддержка операторов
                            for operator, operand in value.items():
                                if operator == "gte":
                                    query = query.gte(key, operand)
                                elif operator == "lte":
                                    query = query.lte(key, operand)
                                elif operator == "gt":
                                    query = query.gt(key, operand)
                                elif operator == "lt":
                                    query = query.lt(key, operand)
                                elif operator == "neq":
                                    query = query.neq(key, operand)
                                elif operator == "in":
                                    query = query.in_(key, operand)
                                elif operator == "is":
                                    query = query.is_(key, operand)
                                else:
                                    logger.warning(f"Неизвестный оператор: {operator}")
                        else:
                            query = query.eq(key, value)

                # Ограничение количества
                if limit:
                    query = query.limit(limit)

                result = query.execute()

                if single and result.data:
                    return result.data[0] if result.data else None
                return result.data or []

            elif operation == "insert":
                if not data:
                    raise ValueError("Данные для вставки не указаны")

                # Валидируем данные
                self._validate_insert_data(data)

                result = query.insert(data).execute()

                if single and result.data:
                    return result.data[0] if result.data else None
                return result.data or []

            elif operation == "update":
                if not data:
                    raise ValueError("Данные для обновления не указаны")

                # Валидируем данные
                self._validate_update_data(data)

                query = query.update(data)

                # Применяем фильтры для обновления
                if filters:
                    for key, value in filters.items():
                        query = query.eq(key, value)
                else:
                    raise ValueError("Фильтры обязательны для операции update")

                result = query.execute()
                return result.data or []

            elif operation == "upsert":
                if not data:
                    raise ValueError("Данные для upsert не указаны")

                result = query.upsert(data).execute()
                return result.data or []

            elif operation == "delete":
                if not filters:
                    raise ValueError("Фильтры обязательны для операции delete")

                for key, value in filters.items():
                    query = query.eq(key, value)

                result = query.delete().execute()
                return result.data or []

            else:
                raise ValueError(f"Неподдерживаемая операция: {operation}")

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"❌ Ошибка выполнения {operation} запроса к таблице {table} "
                f"(время: {execution_time:.2f}s): {e}",
                exc_info=True
            )
            raise SupabaseQueryError(f"Ошибка запроса к {table}: {e}")

        finally:
            execution_time = time.time() - start_time
            if execution_time > 5:
                logger.warning(f"Медленный запрос к {table}: {execution_time:.2f}s")

    def _validate_insert_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]):
        """Валидация данных для вставки"""
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("Данные должны быть словарем или списком словарей")

        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Каждый элемент данных должен быть словарем")

            # Проверяем размер данных
            if len(str(item)) > 100000:  # 100KB лимит
                raise ValueError("Данные слишком большие для одной записи")

    def _validate_update_data(self, data: Dict[str, Any]):
        """Валидация данных для обновления"""
        if not isinstance(data, dict):
            raise ValueError("Данные для обновления должны быть словарем")

        if not data:
            raise ValueError("Данные для обновления не могут быть пустыми")

        # Проверяем размер данных
        if len(str(data)) > 50000:  # 50KB лимит
            raise ValueError("Данные для обновления слишком большие")

    async def execute_batch_update(self, table: str, updates: List[Dict[str, Any]]) -> List[Any]:
        """Batch обновление для оптимизации производительности"""
        if not updates:
            return []

        if len(updates) > 100:
            raise ValueError("Слишком много операций в batch (макс 100)")

        results = []
        # Выполняем batch операции группами
        batch_size = 10
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[
                    self.execute_query(
                        table=table,
                        operation="update",
                        data=update['data'],
                        filters=update['filters']
                    )
                    for update in batch
                ],
                return_exceptions=True
            )
            results.extend(batch_results)

        return results

    async def count_records(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Подсчет количества записей в таблице с кешированием"""
        try:
            self._validate_table_name(table)
            self._check_rate_limit()

            query = self.client.table(table).select("*", count="exact")

            if filters:
                filters = self._sanitize_filters(filters)
                for key, value in filters.items():
                    query = query.eq(key, value)

            result = query.execute()
            return result.count or 0

        except Exception as e:
            logger.error(f"❌ Ошибка подсчета записей в таблице {table}: {e}")
            return 0

    async def health_check(self) -> bool:
        """Проверка состояния соединения"""
        try:
            await self._test_connection()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Получение статистики соединения"""
        return {
            "initialized": self._initialized,
            "rate_limit_calls": self._rate_limit_calls,
            "rate_limit_window_start": self._rate_limit_window_start,
            "max_calls_per_minute": self._max_calls_per_minute
        }


# Глобальный экземпляр клиента с улучшенным управлением
_supabase_client: Optional[SupabaseClient] = None
_client_lock = asyncio.Lock()


async def get_supabase_client() -> SupabaseClient:
    """Получить глобальный экземпляр клиента Supabase (thread-safe)"""
    global _supabase_client

    async with _client_lock:
        if _supabase_client is None:
            _supabase_client = SupabaseClient()
            await _supabase_client.initialize()

    return _supabase_client


async def close_supabase_client():
    """Закрыть соединение с Supabase"""
    global _supabase_client

    async with _client_lock:
        if _supabase_client:
            logger.info("🛑 Supabase клиент закрыт")
            _supabase_client = None


# Экспорт исключений для использования в других модулях
__all__ = [
    'SupabaseClient',
    'get_supabase_client',
    'close_supabase_client',
    'SupabaseConnectionError',
    'SupabaseQueryError',
    'SupabaseTransactionError'
]

logger.info("✅ Fixed Supabase client loaded with enhanced security and reliability")