"""
Кастомные исключения для улучшенной обработки ошибок
Заменяет общие Exception на специфические
"""

from typing import Optional, Any, Dict
from enum import Enum


class ErrorCode(Enum):
    """Коды ошибок для клиентского API"""
    # Пользователи
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    INVALID_USER_DATA = "INVALID_USER_DATA"

    # Ресурсы
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    INSUFFICIENT_ENERGY = "INSUFFICIENT_ENERGY"
    INVALID_AMOUNT = "INVALID_AMOUNT"

    # База данных
    DATABASE_ERROR = "DATABASE_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    TRANSACTION_ERROR = "TRANSACTION_ERROR"

    # Валидация
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"

    # Авторизация
    ACCESS_DENIED = "ACCESS_DENIED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Игровая логика
    QUEST_NOT_AVAILABLE = "QUEST_NOT_AVAILABLE"
    TUTORIAL_STEP_INVALID = "TUTORIAL_STEP_INVALID"
    FEATURE_DISABLED = "FEATURE_DISABLED"


class RyabotException(Exception):
    """Базовое исключение для всего проекта"""

    def __init__(
            self,
            message: str,
            error_code: Optional[ErrorCode] = None,
            details: Optional[Dict[str, Any]] = None,
            user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.user_message = user_message or message
        self.timestamp = None  # Будет установлено при логировании


# ========== ИСКЛЮЧЕНИЯ ПОЛЬЗОВАТЕЛЕЙ ==========

class UserException(RyabotException):
    """Базовое исключение для пользователей"""
    pass


class UserNotFoundError(UserException):
    """Пользователь не найден"""

    def __init__(self, user_id: int):
        super().__init__(
            message=f"Пользователь {user_id} не найден",
            error_code=ErrorCode.USER_NOT_FOUND,
            details={"user_id": user_id},
            user_message="Пользователь не найден. Используйте /start для регистрации"
        )


class UserAlreadyExistsError(UserException):
    """Пользователь уже существует"""

    def __init__(self, user_id: int):
        super().__init__(
            message=f"Пользователь {user_id} уже существует",
            error_code=ErrorCode.USER_ALREADY_EXISTS,
            details={"user_id": user_id},
            user_message="Ваш аккаунт уже зарегистрирован"
        )


class InvalidUserDataError(UserException):
    """Некорректные данные пользователя"""

    def __init__(self, field: str, value: Any, reason: str = ""):
        super().__init__(
            message=f"Некорректное значение для {field}: {value}. {reason}",
            error_code=ErrorCode.INVALID_USER_DATA,
            details={"field": field, "value": value, "reason": reason},
            user_message=f"Некорректные данные: {reason}"
        )


# ========== ИСКЛЮЧЕНИЯ РЕСУРСОВ ==========

class ResourceException(RyabotException):
    """Базовое исключение для ресурсов"""
    pass


class InsufficientFundsError(ResourceException):
    """Недостаточно средств"""

    def __init__(self, resource_type: str, required: int, available: int):
        super().__init__(
            message=f"Недостаточно {resource_type}: нужно {required}, доступно {available}",
            error_code=ErrorCode.INSUFFICIENT_FUNDS,
            details={
                "resource_type": resource_type,
                "required": required,
                "available": available
            },
            user_message=f"💰 Недостаточно {resource_type}! Нужно {required:,}, у вас {available:,}"
        )


class InsufficientEnergyError(ResourceException):
    """Недостаточно энергии"""

    def __init__(self, required: int, available: int):
        super().__init__(
            message=f"Недостаточно энергии: нужно {required}, доступно {available}",
            error_code=ErrorCode.INSUFFICIENT_ENERGY,
            details={"required": required, "available": available},
            user_message=f"⚡ Недостаточно энергии! Нужно {required}, у вас {available}"
        )


class InvalidAmountError(ResourceException):
    """Некорректная сумма"""

    def __init__(self, amount: Any, reason: str = ""):
        super().__init__(
            message=f"Некорректная сумма: {amount}. {reason}",
            error_code=ErrorCode.INVALID_AMOUNT,
            details={"amount": amount, "reason": reason},
            user_message=f"Некорректная сумма. {reason}"
        )


# ========== ИСКЛЮЧЕНИЯ БАЗЫ ДАННЫХ ==========

class DatabaseException(RyabotException):
    """Базовое исключение для БД"""
    pass


class ConnectionError(DatabaseException):
    """Ошибка подключения к БД"""

    def __init__(self, service: str, details: str = ""):
        super().__init__(
            message=f"Ошибка подключения к {service}: {details}",
            error_code=ErrorCode.CONNECTION_ERROR,
            details={"service": service, "connection_details": details},
            user_message="Временные проблемы с сервером. Попробуйте позже"
        )


class TransactionError(DatabaseException):
    """Ошибка транзакции БД"""

    def __init__(self, operation: str, reason: str = ""):
        super().__init__(
            message=f"Ошибка транзакции {operation}: {reason}",
            error_code=ErrorCode.TRANSACTION_ERROR,
            details={"operation": operation, "reason": reason},
            user_message="Операция не выполнена. Попробуйте еще раз"
        )


class QueryError(DatabaseException):
    """Ошибка выполнения запроса"""

    def __init__(self, query_type: str, table: str, reason: str = ""):
        super().__init__(
            message=f"Ошибка {query_type} запроса к таблице {table}: {reason}",
            error_code=ErrorCode.DATABASE_ERROR,
            details={"query_type": query_type, "table": table, "reason": reason},
            user_message="Ошибка обработки данных. Обратитесь в поддержку"
        )


# ========== ИСКЛЮЧЕНИЯ ВАЛИДАЦИИ ==========

class ValidationException(RyabotException):
    """Базовое исключение для валидации"""
    pass


class ValidationError(ValidationException):
    """Ошибка валидации данных"""

    def __init__(self, field: str, value: Any, constraint: str):
        super().__init__(
            message=f"Валидация поля {field} провалилась: {value} не соответствует {constraint}",
            error_code=ErrorCode.VALIDATION_ERROR,
            details={"field": field, "value": value, "constraint": constraint},
            user_message=f"Некорректное значение для {field}: {constraint}"
        )


class InvalidInputError(ValidationException):
    """Некорректный ввод пользователя"""

    def __init__(self, input_type: str, expected: str, received: str):
        super().__init__(
            message=f"Некорректный ввод {input_type}: ожидался {expected}, получен {received}",
            error_code=ErrorCode.INVALID_INPUT,
            details={"input_type": input_type, "expected": expected, "received": received},
            user_message=f"Некорректный ввод. Ожидался {expected}"
        )


# ========== ИСКЛЮЧЕНИЯ АВТОРИЗАЦИИ ==========

class AuthException(RyabotException):
    """Базовое исключение для авторизации"""
    pass


class AccessDeniedError(AuthException):
    """Доступ запрещен"""

    def __init__(self, resource: str, user_id: Optional[int] = None, reason: str = ""):
        super().__init__(
            message=f"Доступ запрещен к {resource} для пользователя {user_id}: {reason}",
            error_code=ErrorCode.ACCESS_DENIED,
            details={"resource": resource, "user_id": user_id, "reason": reason},
            user_message=f"🚫 Доступ запрещен. {reason}"
        )


class RateLimitExceededError(AuthException):
    """Превышен лимит запросов"""

    def __init__(self, limit: int, window: str, user_id: Optional[int] = None):
        super().__init__(
            message=f"Превышен rate limit {limit} запросов в {window} для пользователя {user_id}",
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            details={"limit": limit, "window": window, "user_id": user_id},
            user_message=f"⏰ Слишком много запросов. Подождите {window}"
        )


# ========== ИГРОВЫЕ ИСКЛЮЧЕНИЯ ==========

class GameException(RyabotException):
    """Базовое исключение для игровой логики"""
    pass


class QuestNotAvailableError(GameException):
    """Квест недоступен"""

    def __init__(self, quest_id: str, reason: str = ""):
        super().__init__(
            message=f"Квест {quest_id} недоступен: {reason}",
            error_code=ErrorCode.QUEST_NOT_AVAILABLE,
            details={"quest_id": quest_id, "reason": reason},
            user_message=f"📋 Задание недоступно. {reason}"
        )


class TutorialStepInvalidError(GameException):
    """Некорректный шаг туториала"""

    def __init__(self, current_step: str, expected_step: str):
        super().__init__(
            message=f"Некорректный шаг туториала: текущий {current_step}, ожидался {expected_step}",
            error_code=ErrorCode.TUTORIAL_STEP_INVALID,
            details={"current_step": current_step, "expected_step": expected_step},
            user_message="Необходимо выполнить предыдущие шаги туториала"
        )


class FeatureDisabledError(GameException):
    """Функция отключена"""

    def __init__(self, feature: str):
        super().__init__(
            message=f"Функция {feature} отключена",
            error_code=ErrorCode.FEATURE_DISABLED,
            details={"feature": feature},
            user_message=f"🚧 Функция временно недоступна: {feature}"
        )


# ========== УТИЛИТАРНЫЕ ФУНКЦИИ ==========

def get_user_friendly_message(exception: Exception) -> str:
    """Получить понятное пользователю сообщение об ошибке"""
    if isinstance(exception, RyabotException):
        return exception.user_message

    # Для стандартных исключений
    error_messages = {
        ValueError: "Некорректные данные",
        TypeError: "Неверный тип данных",
        KeyError: "Отсутствует обязательный параметр",
        AttributeError: "Ошибка в структуре данных",
        ConnectionError: "Проблемы с подключением",
        TimeoutError: "Превышено время ожидания"
    }

    return error_messages.get(type(exception), "Произошла неизвестная ошибка")


def is_retryable_error(exception: Exception) -> bool:
    """Определить, можно ли повторить операцию после этой ошибки"""
    retryable_exceptions = (
        ConnectionError,
        TransactionError,
        TimeoutError
    )

    if isinstance(exception, retryable_exceptions):
        return True

    # Также проверяем стандартные исключения
    retryable_standard = (
        ConnectionError,
        TimeoutError
    )

    return isinstance(exception, retryable_standard)


def get_error_severity(exception: Exception) -> str:
    """Получить уровень серьезности ошибки для логирования"""
    if isinstance(exception, (
            UserNotFoundError,
            InvalidInputError,
            InsufficientFundsError,
            InsufficientEnergyError
    )):
        return "INFO"  # Обычные игровые ситуации

    if isinstance(exception, (
            ValidationError,
            InvalidUserDataError,
            QuestNotAvailableError
    )):
        return "WARNING"  # Требуют внимания

    if isinstance(exception, (
            DatabaseException,
            ConnectionError,
            TransactionError
    )):
        return "ERROR"  # Серьезные проблемы

    return "ERROR"  # По умолчанию