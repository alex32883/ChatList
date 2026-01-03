"""
Модуль для отправки HTTP-запросов к API различных нейросетей.
Обрабатывает запросы к OpenAI, Groq и другим API.
"""
import requests
import time
from typing import Dict, Optional, Any
from config import get_api_key, get_timeout, DEFAULT_MODEL_CONFIGS
import logger


class APIError(Exception):
    """Исключение для ошибок API."""
    pass


def send_openai_request(model_name: str, prompt: str, api_key: str, 
                       timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Отправляет запрос к OpenAI API.
    
    Args:
        model_name: Название модели (например, 'gpt-4', 'gpt-3.5-turbo')
        prompt: Текст промта
        api_key: API-ключ OpenAI
        timeout: Таймаут запроса в секундах
    
    Returns:
        Словарь с ответом API, содержащий:
        - 'response': текст ответа
        - 'tokens_used': количество использованных токенов
        - 'response_time': время ответа в секундах
    
    Raises:
        APIError: При ошибке запроса
    """
    if timeout is None:
        timeout = get_timeout()
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        response_time = time.time() - start_time
        
        data = response.json()
        content = data['choices'][0]['message']['content']
        tokens_used = data.get('usage', {}).get('total_tokens')
        
        result = {
            'response': content,
            'tokens_used': tokens_used,
            'response_time': response_time
        }
        logger.log_api_request(model_name, prompt, True, tokens_used=tokens_used, response_time=response_time)
        return result
    except requests.exceptions.RequestException as e:
        error_msg = f"OpenAI API error: {str(e)}"
        logger.log_api_request(model_name, prompt, False, error=error_msg)
        raise APIError(error_msg)
    except (KeyError, IndexError) as e:
        error_msg = f"Unexpected response format from OpenAI API: {str(e)}"
        logger.log_api_request(model_name, prompt, False, error=error_msg)
        raise APIError(error_msg)


def send_groq_request(model_name: str, prompt: str, api_key: str,
                     timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Отправляет запрос к Groq API.
    
    Args:
        model_name: Название модели (например, 'llama-3-70b-8192')
        prompt: Текст промта
        api_key: API-ключ Groq
        timeout: Таймаут запроса в секундах
    
    Returns:
        Словарь с ответом API, содержащий:
        - 'response': текст ответа
        - 'tokens_used': количество использованных токенов
        - 'response_time': время ответа в секундах
    
    Raises:
        APIError: При ошибке запроса
    """
    if timeout is None:
        timeout = get_timeout()
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        response_time = time.time() - start_time
        
        data = response.json()
        content = data['choices'][0]['message']['content']
        tokens_used = data.get('usage', {}).get('total_tokens')
        
        result = {
            'response': content,
            'tokens_used': tokens_used,
            'response_time': response_time
        }
        logger.log_api_request(model_name, prompt, True, tokens_used=tokens_used, response_time=response_time)
        return result
    except requests.exceptions.RequestException as e:
        error_msg = f"Groq API error: {str(e)}"
        logger.log_api_request(model_name, prompt, False, error=error_msg)
        raise APIError(error_msg)
    except (KeyError, IndexError) as e:
        error_msg = f"Unexpected response format from Groq API: {str(e)}"
        logger.log_api_request(model_name, prompt, False, error=error_msg)
        raise APIError(error_msg)


def send_openrouter_request(model_name: str, prompt: str, api_key: str,
                           timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Отправляет запрос к OpenRouter API.
    
    Args:
        model_name: Название модели (например, 'meta-llama/llama-3.3-70b-instruct:free')
        prompt: Текст промта
        api_key: API-ключ OpenRouter
        timeout: Таймаут запроса в секундах
    
    Returns:
        Словарь с ответом API, содержащий:
        - 'response': текст ответа
        - 'tokens_used': количество использованных токенов
        - 'response_time': время ответа в секундах
    
    Raises:
        APIError: При ошибке запроса
    """
    if timeout is None:
        timeout = get_timeout()
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/your-repo",  # Опционально, для отслеживания
        "X-Title": "Chatlist App"  # Опционально
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        response_time = time.time() - start_time
        
        data = response.json()
        content = data['choices'][0]['message']['content']
        tokens_used = data.get('usage', {}).get('total_tokens')
        
        result = {
            'response': content,
            'tokens_used': tokens_used,
            'response_time': response_time
        }
        logger.log_api_request(model_name, prompt, True, tokens_used=tokens_used, response_time=response_time)
        return result
    except requests.exceptions.RequestException as e:
        error_msg = f"OpenRouter API error: {str(e)}"
        logger.log_api_request(model_name, prompt, False, error=error_msg)
        raise APIError(error_msg)
    except (KeyError, IndexError) as e:
        error_msg = f"Unexpected response format from OpenRouter API: {str(e)}"
        logger.log_api_request(model_name, prompt, False, error=error_msg)
        raise APIError(error_msg)


def send_request(model_type: str, model_name: str, prompt: str, api_key: str,
                timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Универсальная функция для отправки запросов к разным API.
    
    Args:
        model_type: Тип API ('openai', 'groq', 'openrouter', и т.д.)
        model_name: Название модели
        prompt: Текст промта
        api_key: API-ключ
        timeout: Таймаут запроса в секундах
    
    Returns:
        Словарь с ответом API
    
    Raises:
        APIError: При ошибке запроса или неподдерживаемом типе API
    """
    if model_type == 'openai':
        # Предупреждение: модели OpenAI требуют правильные идентификаторы (gpt-4, gpt-3.5-turbo)
        # и прямой доступ к OpenAI API. Рекомендуется использовать OpenRouter вместо этого.
        logger.log_info(f"Using OpenAI API directly for model: {model_name}")
        return send_openai_request(model_name, prompt, api_key, timeout)
    elif model_type == 'groq':
        return send_groq_request(model_name, prompt, api_key, timeout)
    elif model_type == 'openrouter':
        return send_openrouter_request(model_name, prompt, api_key, timeout)
    else:
        raise APIError(f"Unsupported model type: {model_type}")


def send_request_to_model(model_info: Dict, prompt: str, 
                         timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Отправляет запрос к модели на основе информации из БД.
    
    Args:
        model_info: Словарь с информацией о модели из БД:
            - 'api_id': имя переменной окружения с API-ключом
            - 'api_url': URL API
            - 'model_type': тип API ('openai', 'groq', и т.д.)
            - 'name': название модели
        prompt: Текст промта
        timeout: Таймаут запроса в секундах
    
    Returns:
        Словарь с ответом API
    
    Raises:
        APIError: При ошибке запроса или отсутствии API-ключа
    """
    from config import get_api_key
    
    api_key = get_api_key(model_info['api_id'])
    if not api_key:
        raise APIError(f"API key not found for {model_info['api_id']}")
    
    model_type = model_info['model_type']
    model_name = model_info['name']
    
    return send_request(model_type, model_name, prompt, api_key, timeout)

