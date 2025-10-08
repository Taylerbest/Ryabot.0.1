"""Утилиты для кодирования/декодирования Base62"""
import base62
import logging

logger = logging.getLogger(__name__)

BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def encode_player_id(player_id: int) -> str:
    """
    Конвертировать player_id в Base62 код

    Args:
        player_id: Числовой ID игрока

    Returns:
        str: Base62 код (например, '3jXN3')
    """
    try:
        return base62.encode(player_id)
    except Exception as e:
        logger.error(f"Ошибка кодирования player_id {player_id}: {e}")
        return str(player_id)  # Fallback на обычный ID


def decode_player_id(code: str) -> int:
    """
    Декодировать Base62 код обратно в player_id

    Args:
        code: Base62 код или обычный числовой ID

    Returns:
        int: player_id или 0 в случае ошибки
    """
    try:
        # Попытка декодировать Base62
        return base62.decode(code)
    except:
        # Если это обычное число - вернуть его
        try:
            return int(code)
        except:
            logger.error(f"Не удалось декодировать код: {code}")
            return 0


def generate_referral_link(player_id: int, bot_username: str) -> str:
    """
    Создать реферальную ссылку с Base62 кодом

    Args:
        player_id: ID игрока
        bot_username: Username бота

    Returns:
        str: Реферальная ссылка
    """
    code = encode_player_id(player_id)
    return f"https://t.me/{bot_username}?start=ref{code}"
