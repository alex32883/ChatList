"""
Модуль для логирования запросов и ошибок.
"""
import logging
import os
from datetime import datetime
from typing import Optional

# Настройка логирования
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, f"chatlist_{datetime.now().strftime('%Y%m%d')}.log")

# Создаем директорию для логов, если её нет
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Настройка форматтера
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Настройка файлового обработчика
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Настройка консольного обработчика
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)

# Создаем логгер
logger = logging.getLogger('Chatlist')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


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


