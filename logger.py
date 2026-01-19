"""
Модуль для логирования запросов и ошибок.
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional

# Импортируем версию
try:
    from version import __version__
except ImportError:
    __version__ = "1.0.1"

# Импортируем функции для получения путей
try:
    from paths import get_log_dir
    LOG_DIR = get_log_dir()
except (ImportError, Exception) as e:
    # Fallback на текущую директорию, если paths.py недоступен
    LOG_DIR = os.path.join(os.path.expanduser("~"), "Chatlist", "logs")
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception:
        # Если и это не работает, используем временную папку
        LOG_DIR = os.path.join(os.environ.get('TEMP', os.environ.get('TMP', '.')), 'Chatlist', 'logs')
        os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"chatlist_{datetime.now().strftime('%Y%m%d')}.log")

# Настройка форматтера
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Настройка консольного обработчика (всегда работает)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)

# Создаем логгер
logger = logging.getLogger('Chatlist')
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)

# Пытаемся добавить файловый обработчик (может не сработать при импорте)
try:
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except (OSError, PermissionError, Exception) as e:
    # Если не удалось создать файловый обработчик, используем только консольный
    # Это может произойти при импорте модуля, когда папка еще не создана
    pass

# Логируем версию при инициализации (если файловый обработчик еще не добавлен, попробуем снова)
try:
    logger.info(f"Chatlist version {__version__} initialized")
except Exception:
    pass


def log_api_request(model_name: str, prompt: str, success: bool, 
                   error: Optional[str] = None, tokens_used: Optional[int] = None,
                   response_time: Optional[float] = None):
    """Логирует запрос к API."""
    if success:
        logger.info(
            f"API Request - Model: {model_name}, "
            f"Tokens: {tokens_used}, "
            f"Time: {response_time:.2f}s, "
            f"Prompt length: {len(prompt)}"
        )
    else:
        logger.error(f"API Request Failed - Model: {model_name}, Error: {error}")


def log_error(error_message: str, exception: Optional[Exception] = None):
    """Логирует ошибку."""
    if exception:
        logger.error(f"{error_message}: {str(exception)}", exc_info=True)
    else:
        logger.error(error_message)


def log_info(message: str):
    """Логирует информационное сообщение."""
    logger.info(message)





