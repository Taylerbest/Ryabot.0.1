# services/tutorial_service.py
"""
Сервис для управления туториалом
"""

import logging
from typing import Optional
from datetime import datetime

from adapters.database.supabase.client import get_supabase_client
from core.domain.entities import TutorialStep

logger = logging.getLogger(__name__)

class TutorialService:
    """Сервис управления туториалом"""
    
    def __init__(self):
        self.client = None
    
    async def _ensure_client(self):
        """Обеспечиваем подключение к БД"""
        if not self.client:
            self.client = await get_supabase_client()
    
    async def get_tutorial_step(self, user_id: int) -> Optional[TutorialStep]:
        """Получить текущий шаг туториала"""
        try:
            await self._ensure_client()
            
            result = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["tutorial_step", "tutorial_completed"],
                filters={"user_id": user_id},
                single=True
            )
            
            if not result:
                return TutorialStep.NOT_STARTED
            
            if result.get('tutorial_completed', False):
                return TutorialStep.COMPLETED
            
            step_value = result.get('tutorial_step', 'not_started')
            return TutorialStep(step_value)
            
        except Exception as e:
            logger.error(f"Ошибка получения шага туториала для {user_id}: {e}")
            return TutorialStep.NOT_STARTED
    
    async def update_tutorial_step(self, user_id: int, step: TutorialStep) -> bool:
        """Обновить шаг туториала"""
        try:
            await self._ensure_client()
            
            completed = (step == TutorialStep.COMPLETED)
            
            result = await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "tutorial_step": step.value,
                    "tutorial_completed": completed,
                    "last_active": datetime.now().isoformat()
                },
                filters={"user_id": user_id}
            )
            
            logger.info(f"Шаг туториала для {user_id} обновлен на {step.value}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Ошибка обновления шага туториала для {user_id}: {e}")
            return False
    
    async def complete_tutorial(self, user_id: int) -> bool:
        """Завершить туториал"""
        try:
            await self._ensure_client()
            
            # Выдаем финальные награды
            current_user = await self.client.execute_query(
                table="users",
                operation="select",
                columns=["ryabucks", "experience", "energy", "energy_max"],
                filters={"user_id": user_id},
                single=True
            )
            
            if current_user:
                new_ryabucks = current_user['ryabucks'] + 200
                new_exp = current_user['experience'] + 100
                new_energy = min(current_user['energy'] + 30, current_user['energy_max'])
                
                await self.client.execute_query(
                    table="users",
                    operation="update",
                    data={
                        "tutorial_step": TutorialStep.COMPLETED.value,
                        "tutorial_completed": True,
                        "ryabucks": new_ryabucks,
                        "experience": new_exp,
                        "energy": new_energy,
                        "last_active": datetime.now().isoformat()
                    },
                    filters={"user_id": user_id}
                )
                
                logger.info(f"Туториал завершен для {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка завершения туториала для {user_id}: {e}")
            return False
    
    async def skip_tutorial(self, user_id: int) -> bool:
        """Пропустить туториал (без наград)"""
        try:
            await self._ensure_client()
            
            result = await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "tutorial_step": TutorialStep.COMPLETED.value,
                    "tutorial_completed": True,
                    "ryabucks": 500,  # Базовые рябаксы
                    "golden_shards": 0,  # Убираем осколок
                    "last_active": datetime.now().isoformat()
                },
                filters={"user_id": user_id}
            )
            
            logger.info(f"Туториал пропущен для {user_id}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Ошибка пропуска туториала для {user_id}: {e}")
            return False
    
    async def reset_tutorial(self, user_id: int) -> bool:
        """Сброс туториала (для администраторов)"""
        try:
            await self._ensure_client()
            
            result = await self.client.execute_query(
                table="users",
                operation="update",
                data={
                    "tutorial_step": TutorialStep.NOT_STARTED.value,
                    "tutorial_completed": False,
                    "character_preset": 1,
                    "ryabucks": 0,
                    "golden_shards": 1,  # Возвращаем осколок
                    "has_employer_license": False,
                    "has_farm_license": False,
                    "last_active": datetime.now().isoformat()
                },
                filters={"user_id": user_id}
            )
            
            # Удаляем всех нанятых рабочих
            await self.client.execute_query(
                table="specialists",
                operation="delete",
                filters={"user_id": user_id}
            )
            
            logger.info(f"Туториал сброшен для {user_id}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Ошибка сброса туториала для {user_id}: {e}")
            return False
    
    def get_next_step_hint(self, current_step: TutorialStep) -> str:
        """Получить подсказку для следующего шага"""
        hints = {
            TutorialStep.NOT_STARTED: "Создайте персонажа для начала приключения!",
            TutorialStep.CHARACTER_CREATION: "Выберите одного из 10 персонажей.",
            TutorialStep.NICKNAME_INPUT: "Придумайте и введите ваш никнейм (3–20 символов).",
            TutorialStep.SHIPWRECK: "Переживите кораблекрушение и найдите золотой осколок.",
            TutorialStep.TAVERN_VISIT: "Посетите таверну у моря и узнайте про осколок.",
            TutorialStep.PAWN_SHOP: "Продайте золотой осколок в ломбарде за 500 рябаксов.",
            TutorialStep.TOWN_HALL_REGISTER: "Зарегистрируйтесь как гражданин в ратуше за 10 рябаксов.",
            TutorialStep.EMPLOYER_LICENSE: "Купите лицензию работодателя за 100 рябаксов.",
            TutorialStep.ACADEMY_HIRE: "Наймите первого рабочего в академии за 30 рябаксов.",
            TutorialStep.WORK_TASK: "Отправьте рабочего выполнить первое задание в 'Рябота'.",
            TutorialStep.CITIZEN_QUEST: "Получите дополнительный опыт у жителя.",
            TutorialStep.TRAIN_SPECIALIST: "Обучите рабочего на специалиста (фермер или строитель).",
            TutorialStep.FARM_LICENSE: "Купите фермерскую лицензию в ратуше за 200 рябаксов.",
            TutorialStep.BUY_LAND: "Возьмите в аренду участок земли в недвижимости.",
            TutorialStep.BUILD_CROP_BED: "Постройте грядку для зерна в 'Строй-Сам'.",
            TutorialStep.PLANT_GRAIN: "Купите семена на рынке и посадите зерно.",
            TutorialStep.BUILD_HENHOUSE: "Постройте курятник для первой курицы.",
            TutorialStep.BUY_CHICKEN: "Купите первую курицу Рябу на рынке.",
            TutorialStep.COMPLETED: "Туториал завершен! Добро пожаловать на остров!"
        }
        
        return hints.get(current_step, "Следуйте инструкциям на экране.")

# Глобальный экземпляр сервиса
tutorial_service = TutorialService()