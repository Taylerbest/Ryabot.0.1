# services/quest_service.py
"""
Сервис системы заданий для Ryabot Island
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from core.domain.entities import TutorialStep, QuestStatus
from config.texts import QUESTS

logger = logging.getLogger(__name__)

class QuestService:
    """Сервис управления системы заданий"""
    
    def __init__(self):
        self.client = None
    
    async def _ensure_client(self):
        """Обеспечиваем подключение к БД"""
        if not self.client:
            self.client = await get_supabase_client()
    
    def _get_quest_for_tutorial_step(self, step: TutorialStep) -> Optional[Dict[str, Any]]:
        """Получить данные задания для шага туториала"""
        quest_mapping = {
            TutorialStep.TASK_HIRE_WORKER: "hire_worker",
            TutorialStep.TASK_FIRST_WORK: "first_work", 
            TutorialStep.TASK_CITIZEN_QUEST: "citizen_quest",
            TutorialStep.TASK_TRAIN_SPECIALIST: "train_specialist",
            TutorialStep.TASK_BUY_FARM_LICENSE: "buy_farm_license",
            TutorialStep.TASK_BUY_LAND: "buy_land",
            TutorialStep.TASK_BUILD_CROP_BED: "build_crop_bed",
            TutorialStep.TASK_PLANT_GRAIN: "plant_grain",
            TutorialStep.TASK_BUILD_HENHOUSE: "build_henhouse",
            TutorialStep.TASK_BUY_CHICKEN: "buy_chicken"
        }
        
        quest_id = quest_mapping.get(step)
        if quest_id and quest_id in QUESTS:
            return {
                "quest_id": quest_id,
                **QUESTS[quest_id],
                "status": QuestStatus.AVAILABLE
            }
        return None
    
    async def get_current_quest(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить текущее активное задание"""
        try:
            await self._ensure_client()
            
            # Получаем текущий шаг туториала
            user_data = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["tutorial_step", "tutorial_completed"],
                filters={"user_id": user_id},
                single=True
            )
            
            if not user_data:
                return None
            
            if user_data.get('tutorial_completed', False):
                return None  # Туториал завершен
            
            current_step = TutorialStep(user_data['tutorial_step'])
            return self._get_quest_for_tutorial_step(current_step)
            
        except Exception as e:
            logger.error(f"Ошибка получения текущего задания для {user_id}: {e}")
            return None
    
    async def get_all_available_quests(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить все доступные задания"""
        try:
            await self._ensure_client()
            
            user_data = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["tutorial_step", "tutorial_completed"],
                filters={"user_id": user_id},
                single=True
            )
            
            if not user_data or user_data.get('tutorial_completed', False):
                return []
            
            current_step = TutorialStep(user_data['tutorial_step'])
            current_quest = self._get_quest_for_tutorial_step(current_step)
            
            return [current_quest] if current_quest else []
            
        except Exception as e:
            logger.error(f"Ошибка получения заданий для {user_id}: {e}")
            return []
    
    async def complete_quest(self, user_id: int, quest_id: str) -> bool:
        """Завершить задание и перейти к следующему"""
        try:
            await self._ensure_client()
            
            # Определяем следующий шаг туториала
            next_step_mapping = {
                "hire_worker": TutorialStep.TASK_FIRST_WORK,
                "first_work": TutorialStep.TASK_CITIZEN_QUEST,
                "citizen_quest": TutorialStep.TASK_TRAIN_SPECIALIST,
                "train_specialist": TutorialStep.TASK_BUY_FARM_LICENSE,
                "buy_farm_license": TutorialStep.TASK_BUY_LAND,
                "buy_land": TutorialStep.TASK_BUILD_CROP_BED,
                "build_crop_bed": TutorialStep.TASK_PLANT_GRAIN,
                "plant_grain": TutorialStep.TASK_BUILD_HENHOUSE,
                "build_henhouse": TutorialStep.TASK_BUY_CHICKEN,
                "buy_chicken": TutorialStep.COMPLETED
            }
            
            next_step = next_step_mapping.get(quest_id, TutorialStep.COMPLETED)
            is_completed = (next_step == TutorialStep.COMPLETED)
            
            # Обновляем в БД
            result = await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "tutorial_step": next_step.value,
                    "tutorial_completed": is_completed,
                    "last_active": datetime.now().isoformat()
                },
                filters={"user_id": user_id}
            )
            
            logger.info(f"Задание {quest_id} завершено для {user_id}, следующий шаг: {next_step.value}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Ошибка завершения задания {quest_id} для {user_id}: {e}")
            return False
    
    async def is_quest_available(self, user_id: int, quest_id: str) -> bool:
        """Проверить доступность задания"""
        current_quest = await self.get_current_quest(user_id)
        return current_quest and current_quest["quest_id"] == quest_id
    
    async def can_access_feature(self, user_id: int, feature: str) -> bool:
        """Проверить доступ к функции/разделу"""
        try:
            await self._ensure_client()
            
            user_data = await self.client.execute_query(
                table="users",
                operation="select", 
                columns=["tutorial_step", "tutorial_completed", "has_island_access"],
                filters={"user_id": user_id},
                single=True
            )
            
            if not user_data:
                return False
            
            # Если туториал завершен, доступ ко всему
            if user_data.get('tutorial_completed', False):
                return True
            
            # Если нет доступа к острову вообще
            if not user_data.get('has_island_access', False):
                return False
            
            current_step = TutorialStep(user_data['tutorial_step'])
            
            # Правила доступа к функциям
            feature_access_rules = {
                "academy_hire": [
                    TutorialStep.TASK_HIRE_WORKER,
                    TutorialStep.TASK_FIRST_WORK,
                    TutorialStep.TASK_CITIZEN_QUEST,
                    TutorialStep.TASK_TRAIN_SPECIALIST
                ],
                "work_sea": [
                    TutorialStep.TASK_FIRST_WORK,
                    TutorialStep.TASK_CITIZEN_QUEST
                ],
                "academy_train": [
                    TutorialStep.TASK_TRAIN_SPECIALIST
                ],
                "townhall_farm_license": [
                    TutorialStep.TASK_BUY_FARM_LICENSE
                ],
                "realestate": [
                    TutorialStep.TASK_BUY_LAND
                ],
                "construction_cropbed": [
                    TutorialStep.TASK_BUILD_CROP_BED
                ],
                "market_seeds": [
                    TutorialStep.TASK_PLANT_GRAIN
                ],
                "farm_garden": [
                    TutorialStep.TASK_PLANT_GRAIN
                ],
                "construction_henhouse": [
                    TutorialStep.TASK_BUILD_HENHOUSE
                ],
                "market_animals": [
                    TutorialStep.TASK_BUY_CHICKEN
                ]
            }
            
            allowed_steps = feature_access_rules.get(feature, [])
            return current_step in allowed_steps
            
        except Exception as e:
            logger.error(f"Ошибка проверки доступа к {feature} для {user_id}: {e}")
            return False

# Глобальный экземпляр
quest_service = QuestService()