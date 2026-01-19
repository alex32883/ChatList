"""
Модуль для загрузки конфигурации из .env файла.
Хранит API-ключи и настройки по умолчанию.
"""
import os
from dotenv import load_dotenv
from typing import Optional
from paths import get_env_file

# Загружаем переменные окружения из .env файла
# Сначала пытаемся загрузить из пользовательской папки, затем из папки приложения
env_file = get_env_file()
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    # Пытаемся загрузить из папки приложения (для портативной версии)
    load_dotenv()


def get_api_key(api_id: str) -> Optional[str]:
    """
    Получает API-ключ по идентификатору из переменных окружения.
    
    Args:
        api_id: Имя переменной окружения (например, 'OPENAI_API_KEY')
    
    Returns:
        Значение API-ключа или None, если не найден
    """
    return os.getenv(api_id)


def get_timeout() -> int:
    """Получает таймаут для API-запросов в секундах."""
    timeout = os.getenv('DEFAULT_TIMEOUT', '30')
    try:
        return int(timeout)
    except ValueError:
        return 30


def get_auto_save_prompts() -> bool:
    """Проверяет, включено ли автоматическое сохранение промтов."""
    value = os.getenv('AUTO_SAVE_PROMPTS', 'false').lower()
    return value in ('true', '1', 'yes')


def get_export_format() -> str:
    """Получает формат экспорта по умолчанию."""
    return os.getenv('EXPORT_FORMAT', 'markdown').lower()


# Настройки по умолчанию для разных типов API
DEFAULT_MODEL_CONFIGS = {
    'openai': {
        'headers': {
            'Content-Type': 'application/json',
        },
        'model_field': 'model',
    },
    'groq': {
        'headers': {
            'Content-Type': 'application/json',
        },
        'model_field': 'model',
    },
    'openrouter': {
        'headers': {
            'Content-Type': 'application/json',
        },
        'model_field': 'model',
    }
}

