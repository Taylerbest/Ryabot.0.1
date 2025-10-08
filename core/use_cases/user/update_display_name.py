import logging
import re
from core.ports.repositories import UserRepository

logger = logging.getLogger(__name__)


class UpdateDisplayNameUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: int, display_name: str) -> tuple[bool, str]:
        """
        Обновить игровое имя пользователя

        Returns:
            tuple[bool, str]: (успех, сообщение)
        """
        try:
            # Валидация длины
            if not display_name or len(display_name) < 3:
                return False, "❌ Имя должно быть не менее 3 символов"

            if len(display_name) > 12:
                return False, "❌ Имя должно быть не более 12 символов"

            # Валидация символов
            if not re.match(r'^[a-zA-Zа-яА-Я0-9_-]+$', display_name):
                return False, "❌ Используй только буквы, цифры, _ и -"

            # Проверка уникальности
            exists = await self.user_repo.check_display_name_exists(display_name)
            if exists:
                return False, "❌ Это имя уже занято"

            # Обновление имени
            success = await self.user_repo.update_display_name(user_id, display_name)

            if success:
                logger.info(f"Обновлено имя для пользователя {user_id}: {display_name}")
                return True, f"✅ Имя изменено на {display_name}!"
            else:
                return False, "❌ Ошибка сохранения имени"

        except Exception as e:
            logger.error(f"Ошибка обновления имени для {user_id}: {e}", exc_info=True)
            return False, "❌ Произошла ошибка"
