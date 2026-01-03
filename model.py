"""
Модуль для работы с моделями нейросетей.
Содержит логику получения активных моделей, валидации настроек и формирования запросов.
"""
from typing import List, Dict, Optional, Tuple
import db
from network import send_request_to_model, APIError

# Маппинг отображаемых имен моделей на реальные идентификаторы для OpenRouter
# Проверьте актуальные модели на https://openrouter.ai/models
# Для бесплатных моделей добавьте :free в конец идентификатора
OPENROUTER_MODEL_MAP = {
    'Llama 3.3 70B': 'meta-llama/llama-3.3-70b-instruct:free',
    'Mistral 7B': 'mistralai/mistral-7b-instruct:free',
    # ВНИМАНИЕ: Следующие модели могут не работать или требовать оплаты
    # Проверьте актуальные идентификаторы на https://openrouter.ai/models
    # И найдите модели с пометкой "free" для бесплатного использования
    'OpenAI GPT-OSS': 'openai/gpt-3.5-turbo',  # Может требовать оплату
    'Qwen3': 'qwen/qwen-2.5-7b-instruct'  # Может требовать оплату
}


def get_active_models() -> List[Dict]:
    """
    Получает список всех активных моделей из БД.
    
    Returns:
        Список словарей с информацией о моделях
    """
    return db.get_active_models()


def get_all_models() -> List[Dict]:
    """
    Получает список всех моделей (включая неактивные).
    
    Returns:
        Список словарей с информацией о моделях
    """
    return db.get_all_models()


def validate_model_settings(model_info: Dict) -> Tuple[bool, Optional[str]]:
    """
    Валидирует настройки модели.
    
    Args:
        model_info: Словарь с информацией о модели
    
    Returns:
        Кортеж (is_valid, error_message)
        is_valid: True если настройки валидны, False иначе
        error_message: Сообщение об ошибке, если есть
    """
    required_fields = ['name', 'api_url', 'api_id', 'model_type']
    
    for field in required_fields:
        if field not in model_info or not model_info[field]:
            return False, f"Missing required field: {field}"
    
    model_type = model_info['model_type']
    supported_types = ['openai', 'groq', 'openrouter']
    
    if model_type not in supported_types:
        return False, f"Unsupported model type: {model_type}. Supported types: {', '.join(supported_types)}"
    
    # Проверка наличия API-ключа
    from config import get_api_key
    api_key = get_api_key(model_info['api_id'])
    if not api_key:
        return False, f"API key not found for {model_info['api_id']}. Please check your .env file."
    
    return True, None


def send_prompt_to_models(prompt: str, model_ids: Optional[List[int]] = None) -> List[Dict]:
    """
    Отправляет промт во все активные модели (или указанные модели).
    
    Args:
        prompt: Текст промта
        model_ids: Список ID моделей для отправки. Если None, отправляет во все активные.
    
    Returns:
        Список словарей с результатами:
        - 'model_id': ID модели
        - 'model_name': название модели
        - 'response': текст ответа (или None при ошибке)
        - 'error': сообщение об ошибке (или None при успехе)
        - 'tokens_used': количество токенов
        - 'response_time': время ответа
    """
    if model_ids:
        models = [db.get_model(mid) for mid in model_ids if db.get_model(mid)]
    else:
        models = get_active_models()
    
    results = []
    
    for model in models:
        model_result = {
            'model_id': model['id'],
            'model_name': model['name'],
            'response': None,
            'error': None,
            'tokens_used': None,
            'response_time': None
        }
        
        # Валидация настроек модели
        is_valid, error_msg = validate_model_settings(model)
        if not is_valid:
            model_result['error'] = error_msg
            results.append(model_result)
            continue
        
        # Отправка запроса
        try:
            # Для OpenRouter используем маппинг имен моделей
            if model['model_type'] == 'openrouter' and model['name'] in OPENROUTER_MODEL_MAP:
                # Создаем временную копию модели с правильным именем для API
                model_for_api = model.copy()
                model_for_api['name'] = OPENROUTER_MODEL_MAP[model['name']]
                response_data = send_request_to_model(model_for_api, prompt)
            else:
                response_data = send_request_to_model(model, prompt)
            model_result['response'] = response_data.get('response')
            model_result['tokens_used'] = response_data.get('tokens_used')
            model_result['response_time'] = response_data.get('response_time')
        except APIError as e:
            model_result['error'] = str(e)
        except Exception as e:
            model_result['error'] = f"Unexpected error: {str(e)}"
        
        results.append(model_result)
    
    return results


def get_model_by_id(model_id: int) -> Optional[Dict]:
    """
    Получает модель по ID.
    
    Args:
        model_id: ID модели
    
    Returns:
        Словарь с информацией о модели или None
    """
    return db.get_model(model_id)


def create_model(name: str, api_url: str, api_id: str, model_type: str, is_active: int = 1) -> int:
    """
    Создает новую модель.
    
    Args:
        name: Название модели
        api_url: URL API
        api_id: Имя переменной окружения с API-ключом
        model_type: Тип API ('openai', 'groq', и т.д.)
        is_active: Активна ли модель (1 - да, 0 - нет)
    
    Returns:
        ID созданной модели
    
    Raises:
        ValueError: При невалидных данных
    """
    model_info = {
        'name': name,
        'api_url': api_url,
        'api_id': api_id,
        'model_type': model_type,
        'is_active': is_active
    }
    
    is_valid, error_msg = validate_model_settings(model_info)
    if not is_valid:
        raise ValueError(error_msg)
    
    return db.create_model(name, api_url, api_id, model_type, is_active)


def update_model(model_id: int, **kwargs) -> bool:
    """
    Обновляет модель.
    
    Args:
        model_id: ID модели
        **kwargs: Поля для обновления (name, api_url, api_id, model_type, is_active)
    
    Returns:
        True если обновление успешно, False иначе
    """
    return db.update_model(model_id, **kwargs)


def toggle_model_active(model_id: int) -> bool:
    """
    Переключает статус активности модели.
    
    Args:
        model_id: ID модели
    
    Returns:
        True если обновление успешно, False иначе
    """
    model = db.get_model(model_id)
    if not model:
        return False
    
    new_status = 0 if model['is_active'] == 1 else 1
    return db.update_model(model_id, is_active=new_status)

