"""
Модуль для работы с базой данных SQLite.
Инкапсулирует все операции с БД.
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple


DB_FILE = "chatlist.db"


def get_connection():
    """Создает и возвращает соединение с базой данных."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
    return conn


def init_database():
    """Инициализация базы данных и создание всех таблиц."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица prompts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            prompt TEXT NOT NULL,
            tags TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts(tags)")
    
    # Таблица models
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            api_url TEXT NOT NULL,
            api_id TEXT NOT NULL,
            model_type TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_name ON models(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active)")
    
    # Таблица results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id INTEGER NOT NULL,
            model_id INTEGER NOT NULL,
            response TEXT NOT NULL,
            saved_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            tokens_used INTEGER,
            response_time REAL,
            FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE RESTRICT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_prompt_id ON results(prompt_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_model_id ON results(model_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_saved_date ON results(saved_date)")
    
    # Таблица settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)")
    
    # Инициализация моделей по умолчанию
    cursor.execute("""
        INSERT OR IGNORE INTO models (name, api_url, api_id, model_type, is_active) VALUES
        ('GPT-4', 'https://api.openai.com/v1/chat/completions', 'OPENAI_API_KEY', 'openai', 1),
        ('GPT-3.5', 'https://api.openai.com/v1/chat/completions', 'OPENAI_API_KEY', 'openai', 1),
        ('Llama 3 70B', 'https://api.groq.com/openai/v1/chat/completions', 'GROQ_API_KEY', 'groq', 1)
    """)
    
    # Инициализация настроек по умолчанию
    default_settings = [
        ('default_timeout', '30'),
        ('auto_save_prompts', 'false'),
        ('export_format', 'markdown')
    ]
    for key, value in default_settings:
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
        """, (key, value))
    
    conn.commit()
    conn.close()


# ========== Функции для работы с таблицей prompts ==========

def create_prompt(prompt_text: str, tags: Optional[str] = None) -> int:
    """Создает новый промт и возвращает его ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO prompts (prompt, tags, date) VALUES (?, ?, ?)
    """, (prompt_text, tags, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    prompt_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return prompt_id


def get_prompt(prompt_id: int) -> Optional[Dict]:
    """Получает промт по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_prompts() -> List[Dict]:
    """Получает все промты, отсортированные по дате (новые первые)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prompts ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_prompts(query: str) -> List[Dict]:
    """Поиск промтов по тексту или тегам."""
    conn = get_connection()
    cursor = conn.cursor()
    search_pattern = f"%{query}%"
    cursor.execute("""
        SELECT * FROM prompts 
        WHERE prompt LIKE ? OR tags LIKE ?
        ORDER BY date DESC
    """, (search_pattern, search_pattern))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_prompt(prompt_id: int, prompt_text: str, tags: Optional[str] = None) -> bool:
    """Обновляет промт."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE prompts SET prompt = ?, tags = ? WHERE id = ?
    """, (prompt_text, tags, prompt_id))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def delete_prompt(prompt_id: int) -> bool:
    """Удаляет промт."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


# ========== Функции для работы с таблицей models ==========

def create_model(name: str, api_url: str, api_id: str, model_type: str, is_active: int = 1) -> int:
    """Создает новую модель и возвращает ее ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO models (name, api_url, api_id, model_type, is_active) 
        VALUES (?, ?, ?, ?, ?)
    """, (name, api_url, api_id, model_type, is_active))
    model_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return model_id


def get_model(model_id: int) -> Optional[Dict]:
    """Получает модель по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_models() -> List[Dict]:
    """Получает все модели."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM models ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_active_models() -> List[Dict]:
    """Получает только активные модели."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM models WHERE is_active = 1 ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_model(model_id: int, name: Optional[str] = None, api_url: Optional[str] = None,
                 api_id: Optional[str] = None, model_type: Optional[str] = None,
                 is_active: Optional[int] = None) -> bool:
    """Обновляет модель."""
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if api_url is not None:
        updates.append("api_url = ?")
        params.append(api_url)
    if api_id is not None:
        updates.append("api_id = ?")
        params.append(api_id)
    if model_type is not None:
        updates.append("model_type = ?")
        params.append(model_type)
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(is_active)
    
    if not updates:
        conn.close()
        return False
    
    params.append(model_id)
    query = f"UPDATE models SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def delete_model(model_id: int) -> bool:
    """Удаляет модель."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


# ========== Функции для работы с таблицей results ==========

def create_result(prompt_id: int, model_id: int, response: str,
                  tokens_used: Optional[int] = None, response_time: Optional[float] = None) -> int:
    """Создает новый результат и возвращает его ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO results (prompt_id, model_id, response, tokens_used, response_time, saved_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (prompt_id, model_id, response, tokens_used, response_time,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    result_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return result_id


def get_result(result_id: int) -> Optional[Dict]:
    """Получает результат по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM results WHERE id = ?", (result_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_results_by_prompt(prompt_id: int) -> List[Dict]:
    """Получает все результаты для конкретного промта."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, m.name as model_name 
        FROM results r
        JOIN models m ON r.model_id = m.id
        WHERE r.prompt_id = ?
        ORDER BY r.saved_date DESC
    """, (prompt_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_results() -> List[Dict]:
    """Получает все результаты."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, m.name as model_name, p.prompt as prompt_text
        FROM results r
        JOIN models m ON r.model_id = m.id
        JOIN prompts p ON r.prompt_id = p.id
        ORDER BY r.saved_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_result(result_id: int) -> bool:
    """Удаляет результат."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM results WHERE id = ?", (result_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


# ========== Функции для работы с таблицей settings ==========

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Получает значение настройки по ключу."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else default


def set_setting(key: str, value: str) -> bool:
    """Устанавливает значение настройки."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value, updated_at) 
        VALUES (?, ?, ?)
    """, (key, value, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return True


def get_all_settings() -> Dict[str, str]:
    """Получает все настройки."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}

