"""
Модуль для управления путями к файлам приложения.
Обеспечивает правильное размещение файлов для установленной и портативной версии.
"""
import os
import sys


def get_app_dir():
    """
    Возвращает путь к директории приложения.
    Для установленной версии - папка установки (где находится exe).
    Для портативной версии - папка с main.py.
    """
    if getattr(sys, 'frozen', False):
        # Если запущено из собранного exe
        return os.path.dirname(sys.executable)
    else:
        # Если запущено из исходников
        return os.path.dirname(os.path.abspath(__file__))


def get_user_data_dir():
    """
    Возвращает путь к папке пользовательских данных.
    Использует AppData\\Local\\Chatlist для Windows.
    """
    try:
        if sys.platform == 'win32':
            appdata = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
            user_data_dir = os.path.join(appdata, 'Chatlist')
        else:
            # Для Linux/Mac
            user_data_dir = os.path.join(os.path.expanduser('~'), '.chatlist')
        
        # Создаем папку, если её нет
        try:
            os.makedirs(user_data_dir, exist_ok=True)
        except (OSError, PermissionError) as e:
            # Если не удалось создать в AppData, используем временную папку
            temp_dir = os.path.join(os.environ.get('TEMP', os.environ.get('TMP', os.path.expanduser('~'))), 'Chatlist')
            try:
                os.makedirs(temp_dir, exist_ok=True)
                user_data_dir = temp_dir
            except Exception:
                # В крайнем случае используем текущую папку пользователя
                user_data_dir = os.path.join(os.path.expanduser('~'), 'Chatlist')
                os.makedirs(user_data_dir, exist_ok=True)
        
        return user_data_dir
    except Exception:
        # Fallback на временную папку
        temp_dir = os.path.join(os.environ.get('TEMP', os.environ.get('TMP', '.')), 'Chatlist')
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir


def get_db_file():
    """Возвращает путь к файлу базы данных."""
    return os.path.join(get_user_data_dir(), 'chatlist.db')


def get_log_dir():
    """Возвращает путь к папке с логами."""
    try:
        log_dir = os.path.join(get_user_data_dir(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    except Exception:
        # Fallback на временную папку для логов
        temp_log_dir = os.path.join(os.environ.get('TEMP', os.environ.get('TMP', '.')), 'Chatlist', 'logs')
        try:
            os.makedirs(temp_log_dir, exist_ok=True)
            return temp_log_dir
        except Exception:
            # В крайнем случае используем текущую директорию
            return os.path.join(os.path.expanduser('~'), 'Chatlist', 'logs')


def get_env_file():
    """Возвращает путь к .env файлу."""
    # Сначала проверяем в папке пользовательских данных
    user_env = os.path.join(get_user_data_dir(), '.env')
    if os.path.exists(user_env):
        return user_env
    
    # Затем в папке приложения (для портативной версии)
    app_env = os.path.join(get_app_dir(), '.env')
    if os.path.exists(app_env):
        return app_env
    
    # Возвращаем путь к папке пользовательских данных для создания нового
    return user_env


def get_icon_path():
    """Возвращает путь к файлу иконки."""
    # Ищем иконку в папке приложения
    icon_path = os.path.join(get_app_dir(), 'app.ico')
    if os.path.exists(icon_path):
        return icon_path
    return None
