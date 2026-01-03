# Схема базы данных Chatlist

## Общая информация

База данных: SQLite  
Файл БД: `chatlist.db` (создается автоматически при первом запуске)

## Таблицы

### 1. Таблица `prompts` (Промты)

Хранит сохраненные пользователем промты (запросы).

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| `id` | INTEGER | Первичный ключ | PRIMARY KEY, AUTOINCREMENT |
| `date` | TEXT | Дата и время создания | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| `prompt` | TEXT | Текст промта | NOT NULL |
| `tags` | TEXT | Теги через запятую | NULL |

**Индексы:**
- `idx_prompts_date` на поле `date`
- `idx_prompts_tags` на поле `tags`

**Пример данных:**
```
id: 1
date: "2024-01-15 10:30:00"
prompt: "Объясни квантовую физику простыми словами"
tags: "наука, физика, объяснение"
```

### 2. Таблица `models` (Модели нейросетей)

Хранит информацию о доступных моделях нейросетей.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| `id` | INTEGER | Первичный ключ | PRIMARY KEY, AUTOINCREMENT |
| `name` | TEXT | Название модели | NOT NULL, UNIQUE |
| `api_url` | TEXT | URL API для запросов | NOT NULL |
| `api_id` | TEXT | Идентификатор API (имя переменной в .env) | NOT NULL |
| `model_type` | TEXT | Тип модели (openai, groq, и т.д.) | NOT NULL |
| `is_active` | INTEGER | Активна ли модель (1 - да, 0 - нет) | NOT NULL, DEFAULT 1 |

**Индексы:**
- `idx_models_name` на поле `name`
- `idx_models_active` на поле `is_active`

**Пример данных:**
```
id: 1
name: "GPT-4"
api_url: "https://api.openai.com/v1/chat/completions"
api_id: "OPENAI_API_KEY"
model_type: "openai"
is_active: 1

id: 2
name: "Llama 3"
api_url: "https://api.groq.com/openai/v1/chat/completions"
api_id: "GROQ_API_KEY"
model_type: "groq"
is_active: 1
```

**Примечание:** Сами API-ключи хранятся в файле `.env`, а в таблице хранится только имя переменной окружения.

### 3. Таблица `results` (Сохраненные результаты)

Хранит сохраненные пользователем результаты ответов моделей.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| `id` | INTEGER | Первичный ключ | PRIMARY KEY, AUTOINCREMENT |
| `prompt_id` | INTEGER | ID промта из таблицы prompts | NOT NULL, FOREIGN KEY |
| `model_id` | INTEGER | ID модели из таблицы models | NOT NULL, FOREIGN KEY |
| `response` | TEXT | Текст ответа модели | NOT NULL |
| `saved_date` | TEXT | Дата и время сохранения | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| `tokens_used` | INTEGER | Количество использованных токенов | NULL |
| `response_time` | REAL | Время ответа в секундах | NULL |

**Индексы:**
- `idx_results_prompt_id` на поле `prompt_id`
- `idx_results_model_id` на поле `model_id`
- `idx_results_saved_date` на поле `saved_date`

**Внешние ключи:**
- `prompt_id` → `prompts(id)` ON DELETE CASCADE
- `model_id` → `models(id)` ON DELETE RESTRICT

**Пример данных:**
```
id: 1
prompt_id: 1
model_id: 1
response: "Квантовая физика изучает поведение частиц..."
saved_date: "2024-01-15 10:35:00"
tokens_used: 150
response_time: 2.5
```

### 4. Таблица `settings` (Настройки программы)

Хранит настройки приложения.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| `id` | INTEGER | Первичный ключ | PRIMARY KEY, AUTOINCREMENT |
| `key` | TEXT | Ключ настройки | NOT NULL, UNIQUE |
| `value` | TEXT | Значение настройки | NULL |
| `updated_at` | TEXT | Дата последнего обновления | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

**Индексы:**
- `idx_settings_key` на поле `key` (UNIQUE)

**Пример данных:**
```
id: 1
key: "default_timeout"
value: "30"
updated_at: "2024-01-15 10:00:00"

id: 2
key: "auto_save_prompts"
value: "true"
updated_at: "2024-01-15 10:00:00"

id: 3
key: "export_format"
value: "markdown"
updated_at: "2024-01-15 10:00:00"
```

## Связи между таблицами

```
prompts (1) ──< (N) results
models  (1) ──< (N) results
```

- Один промт может иметь множество сохраненных результатов
- Одна модель может иметь множество сохраненных результатов
- Каждый результат связан с одним промтом и одной моделью

## SQL для создания таблиц

```sql
-- Таблица prompts
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    prompt TEXT NOT NULL,
    tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date);
CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts(tags);

-- Таблица models
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_url TEXT NOT NULL,
    api_id TEXT NOT NULL,
    model_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_models_name ON models(name);
CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active);

-- Таблица results
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
);

CREATE INDEX IF NOT EXISTS idx_results_prompt_id ON results(prompt_id);
CREATE INDEX IF NOT EXISTS idx_results_model_id ON results(model_id);
CREATE INDEX IF NOT EXISTS idx_results_saved_date ON results(saved_date);

-- Таблица settings
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);
```

## Инициализация данных

При первом запуске программы рекомендуется добавить несколько моделей по умолчанию:

```sql
INSERT OR IGNORE INTO models (name, api_url, api_id, model_type, is_active) VALUES
('GPT-4', 'https://api.openai.com/v1/chat/completions', 'OPENAI_API_KEY', 'openai', 1),
('GPT-3.5', 'https://api.openai.com/v1/chat/completions', 'OPENAI_API_KEY', 'openai', 1),
('Llama 3 70B', 'https://api.groq.com/openai/v1/chat/completions', 'GROQ_API_KEY', 'groq', 1);
```



