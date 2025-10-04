# adapters/database/supabase/client.py
"""
Клиент для работы с Supabase
Обертка над официальной библиотекой supabase
"""

import asyncio
from typing import Optional, Dict, Any, List, Union
import logging
from supabase import create_client, Client

from config.settings import settings

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Клиент для работы с Supabase"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialized = False
    
    async def initialize(self):
        """Инициализация соединения"""
        if self._initialized:
            return
        
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise ValueError("SUPABASE_URL и SUPABASE_ANON_KEY должны быть установлены в .env")
        
        try:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            logger.info("✅ Supabase клиент инициализирован")
            self._initialized = True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Supabase: {e}")
            raise
    
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
        Выполнение запроса к Supabase
        
        Args:
            table: Название таблицы
            operation: Тип операции (select, insert, update, delete)
            data: Данные для вставки/обновления
            filters: Фильтры для запроса
            single: Вернуть одну запись вместо списка
            limit: Ограничение количества записей
            columns: Список колонок для выборки
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            query = self.client.table(table)
            
            if operation == "select":
                # Выборка данных
                if columns:
                    query = query.select(",".join(columns))
                else:
                    query = query.select("*")
                
                # Применяем фильтры
                if filters:
                    for key, value in filters.items():
                        if isinstance(value, dict):
                            # Поддержка операторов типа {"gte": "2023-01-01"}
                            if "gte" in value:
                                query = query.gte(key, value["gte"])
                            elif "lte" in value:
                                query = query.lte(key, value["lte"])
                            elif "gt" in value:
                                query = query.gt(key, value["gt"])
                            elif "lt" in value:
                                query = query.lt(key, value["lt"])
                            elif "neq" in value:
                                query = query.neq(key, value["neq"])
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
                # Вставка данных
                if not data:
                    raise ValueError("Данные для вставки не указаны")
                
                result = query.insert(data).execute()
                
                if single and result.data:
                    return result.data[0] if result.data else None
                return result.data or []
            
            elif operation == "update":
                # Обновление данных
                if not data:
                    raise ValueError("Данные для обновления не указаны")
                
                query = query.update(data)
                
                # Применяем фильтры для обновления
                if filters:
                    for key, value in filters.items():
                        query = query.eq(key, value)
                
                result = query.execute()
                return result.data or []
            
            elif operation == "delete":
                # Удаление данных
                if filters:
                    for key, value in filters.items():
                        query = query.eq(key, value)
                
                result = query.delete().execute()
                return result.data or []
            
            else:
                raise ValueError(f"Неподдерживаемая операция: {operation}")
        
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения запроса к таблице {table}: {e}")
            raise
    
    async def count_records(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Подсчет количества записей в таблице"""
        try:
            query = self.client.table(table).select("*", count="exact")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            result = query.execute()
            return result.count or 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка подсчета записей в таблице {table}: {e}")
            return 0

# Глобальный экземпляр клиента
_supabase_client: Optional[SupabaseClient] = None

async def get_supabase_client() -> SupabaseClient:
    """Получить глобальный экземпляр клиента Supabase"""
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
        await _supabase_client.initialize()
    
    return _supabase_client

async def close_supabase_client():
    """Закрыть соединение с Supabase"""
    global _supabase_client
    
    if _supabase_client:
        # Supabase клиент не требует явного закрытия
        logger.info("🛑 Supabase клиент закрыт")
        _supabase_client = None