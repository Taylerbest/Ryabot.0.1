# services/blockchain_service.py
"""
Сервис логирования действий в блокчейн и уведомления в каналы
"""

import logging
import hashlib
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from adapters.database.supabase.client import get_supabase_client
from config.settings import settings

logger = logging.getLogger(__name__)

class BlockchainService:
    """Сервис блокчейн аудита и уведомлений"""
    
    def __init__(self):
        self.client = None
        
    async def _ensure_client(self):
        """Обеспечиваем подключение к БД"""
        if not self.client:
            self.client = await get_supabase_client()
    
    def _calculate_hash(self, prev_hash: str, payload: Dict[str, Any], timestamp: float) -> str:
        """Вычислить хеш блока"""
        data = f"{prev_hash}{json.dumps(payload, sort_keys=True)}{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def _get_last_hash(self) -> str:
        """Получить хеш последнего блока"""
        try:
            await self._ensure_client()
            
            last_entry = await self.client.execute_query(
                table="audit_log",
                operation="select",
                columns=["hash"],
                limit=1
            )
            
            if last_entry:
                return last_entry[0]['hash']
            return "genesis"
            
        except Exception as e:
            logger.error(f"Ошибка получения последнего хеша: {e}")
            return "genesis"
    
    def _format_blockchain_message(self, action_type: str, username: str, payload: Dict[str, Any], 
                                 current_hash: str, prev_hash: str) -> str:
        """Форматирование сообщения для блокчейн канала"""
        
        # Эмодзи для разных действий
        action_emojis = {
            "SHARD_SOLD": "💎",
            "CITIZEN_REGISTERED": "🏛️",
            "LICENSE_PURCHASED": "📜", 
            "WORKER_HIRED": "👷",
            "WORK_COMPLETED": "💼",
            "SPECIALIST_TRAINED": "🎓",
            "BUILDING_BUILT": "🏗️",
            "ANIMAL_BOUGHT": "🐔",
            "GOLDEN_EGG_FOUND": "🥚",
            "RBTC_EARNED": "💠",
            "EXPEDITION_COMPLETED": "🗺️",
            "ACHIEVEMENT_UNLOCKED": "🏆"
        }
        
        emoji = action_emojis.get(action_type, "⚡")
        
        # Детали действия
        details = []
        if action_type == "SHARD_SOLD":
            details.append(f"Цена: {payload.get('price', 0)} {payload.get('currency', 'рябаксов')}")
        elif action_type == "CITIZEN_REGISTERED":
            details.append(f"Сбор: {payload.get('fee_paid', 0)} рябаксов")
        elif action_type == "LICENSE_PURCHASED":
            details.append(f"Тип: {payload.get('license_type', 'неизвестно')} LV{payload.get('level', 1)}")
            details.append(f"Цена: {payload.get('price', 0)} рябаксов")
        elif action_type == "WORKER_HIRED":
            details.append(f"Имя: {payload.get('name', 'Неизвестный')}")
            details.append(f"Стоимость: {payload.get('cost', 0)} рябаксов")
        elif action_type == "WORK_COMPLETED":
            details.append(f"Задание: {payload.get('task', 'неизвестно')}")
            details.append(f"Награда: {payload.get('reward_money', 0)} рябаксов")
        
        detail_text = " | ".join(details) if details else ""
        
        return f"""
{emoji} **{action_type.replace('_', ' ').title()}**

👤 Игрок: @{username}
📝 Детали: {detail_text}
⏰ Время: {datetime.now().strftime('%H:%M:%S')}

🔗 Hash: `{current_hash[:16]}...`
🔗 Prev: `{prev_hash[:16]}...`
        """.strip()
    
    def _format_celebration_message(self, action_type: str, username: str, payload: Dict[str, Any]) -> str:
        """Форматирование праздничного сообщения для основного канала"""
        
        if action_type == "CITIZEN_REGISTERED":
            return f"""
🎉 **НОВЫЙ ЖИТЕЛЬ ОСТРОВА!**

👋 Добро пожаловать, @{username}!
🏝️ Теперь вы официальный гражданин острова Ryabot!

🎯 Начните свой путь:
• 👷 Наймите первого рабочего
• 🐔 Постройте ферму  
• 💠 Зарабатывайте RBTC

#НовыйЖитель #RyabotIsland
            """.strip()
            
        elif action_type == "GOLDEN_EGG_FOUND":
            return f"""
🥚✨ **ЗОЛОТОЕ ЯЙЦО НАЙДЕНО!** ✨🥚

🎊 @{username} нашёл легендарное золотое яйцо!
💰 Награда: {payload.get('rbtc_reward', '0')} RBTC

🍀 Вероятность находки: 0.05% 
🏆 Это настоящая удача!

#ЗолотоеЯйцо #Легендарка #RyabotIsland
            """.strip()
            
        elif action_type == "EXPEDITION_COMPLETED":
            difficulty = payload.get('difficulty', 'неизвестная')
            return f"""
🗺️ **ЭКСПЕДИЦИЯ ЗАВЕРШЕНА!**

⚔️ @{username} успешно завершил экспедицию!
📊 Сложность: {difficulty.title()}
💎 Найдено RBTC: {payload.get('rbtc_found', '0')}
🎒 Предметы: {payload.get('items_found', 0)}

#Экспедиция #RyabotIsland
            """.strip()
            
        else:
            return f"🎉 @{username} совершил {action_type.replace('_', ' ').lower()}!"
    
    async def log_action(self, action_type: str, user_id: int, username: str, 
                        payload: Dict[str, Any], significance: int = 0) -> Optional[int]:
        """
        Логировать действие в блокчейн
        
        Args:
            action_type: Тип действия
            user_id: ID пользователя  
            username: Имя пользователя
            payload: Данные о действии
            significance: Значимость (0-обычное, 1-важное, 2-эпическое, 3-легендарное)
        
        Returns:
            ID сообщения в канале или None при ошибке
        """
        try:
            await self._ensure_client()
            
            # Получаем предыдущий хеш
            prev_hash = await self._get_last_hash()
            
            # Вычисляем текущий хеш
            timestamp = time.time()
            current_hash = self._calculate_hash(prev_hash, payload, timestamp)
            
            # Сохраняем в БД
            audit_data = {
                "user_id": user_id,
                "action_type": action_type,
                "payload": payload,
                "hash": current_hash,
                "prev_hash": prev_hash,
                "significance": significance,
                "created_at": datetime.now().isoformat()
            }
            
            result = await self.client.execute_query(
                table="audit_log",
                operation="insert",
                data=audit_data,
                single=True
            )
            
            # Отправляем в канал истории (все события)
            blockchain_msg = None
            bot = Bot(token=settings.BOT_TOKEN)
            
            try:
                if settings.HISTORY_CHANNEL_ID:
                    blockchain_message = self._format_blockchain_message(
                        action_type, username, payload, current_hash, prev_hash
                    )
                    
                    blockchain_msg = await bot.send_message(
                        chat_id=settings.HISTORY_CHANNEL_ID,
                        text=blockchain_message,
                        parse_mode="Markdown"
                    )
                    
                    # Обновляем ID сообщения в БД
                    if result and blockchain_msg:
                        await self.client.execute_query(
                            table="audit_log", 
                            operation="update",
                            data={"tg_message_id": blockchain_msg.message_id},
                            filters={"id": result['id']}
                        )
                        
            except Exception as e:
                logger.error(f"Ошибка отправки в канал истории: {e}")
            
            # Отправляем в основной канал (только эпические и легендарные)
            try:
                if significance >= 2 and settings.ISLAND_CHANNEL_ID:
                    celebration_message = self._format_celebration_message(
                        action_type, username, payload
                    )
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="🔍 Детали в блокчейне", 
                            url=blockchain_msg.link if blockchain_msg else "https://t.me/ryabot_history"
                        )]
                    ])
                    
                    await bot.send_message(
                        chat_id=settings.ISLAND_CHANNEL_ID,
                        message_thread_id=1,  # General topic
                        text=celebration_message,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    
            except Exception as e:
                logger.error(f"Ошибка отправки в основной канал: {e}")
            
            logger.info(f"Действие {action_type} пользователя {username} залогировано")
            return blockchain_msg.message_id if blockchain_msg else None
            
        except Exception as e:
            logger.error(f"Ошибка логирования действия {action_type}: {e}")
            return None

# Глобальный экземпляр сервиса
blockchain_service = BlockchainService()