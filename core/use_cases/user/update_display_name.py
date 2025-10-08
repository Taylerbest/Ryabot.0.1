import logging
from core.ports.repositories import UserRepository

logger = logging.getLogger(__name__)


class UpdateDisplayNameUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: int, display_name: str) -> tuple[bool, str]:
        """
        Обновление отображаемого имени игрока

        Returns:
            tuple[bool, str]: (успех, сообщение)
        """
        # Валидация
        if not display_name or len(display_name) < 3:
            return False, "Имя должно быть не менее 3 символов"

        if len(display_name) > 20:
            return False, "Имя должно быть не более 20 символов"

        # Обновление
        success = await self.user_repo.update_display_name(user_id, display_name)

        if success:
            return True, "Имя успешно изменено!"
        else:
            return False, "Это имя уже занято другим игроком"
