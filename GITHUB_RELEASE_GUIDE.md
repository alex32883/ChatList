# Инструкция по публикации приложения на GitHub Release

## Подготовка к публикации

### 1. Создание репозитория на GitHub

1. Создайте новый репозиторий на GitHub: https://github.com/new
2. Назовите репозиторий (например, `Chatlist`)
3. Добавьте описание: "Приложение для сравнения ответов нейросетей"
4. Выберите публичный или приватный репозиторий
5. **Не** инициализируйте с README (если у вас уже есть файлы)

### 2. Настройка .gitignore

Убедитесь, что файл `.gitignore` содержит:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Database
*.db
*.sqlite

# Environment variables
.env
.env.local

# Build artifacts
installer/
*.exe
*.spec.bak
build_exe.bat.bak

# Temporary files
temp_version.txt
setup_temp.iss
*.iss.bak
```

### 3. Инициализация Git (если еще не сделано)

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/ВАШ_USERNAME/Chatlist.git
git push -u origin main
```

## Создание Release

### Способ 1: Через GitHub Web Interface (Ручной)

1. **Обновите версию в `version.py`**:
   ```python
   __version__ = "1.0.1"
   ```

2. **Соберите инсталлятор**:
   ```bash
   build_installer.bat
   ```

3. **Создайте тег версии**:
   ```bash
   git add version.py
   git commit -m "Bump version to 1.0.1"
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin main
   git push origin v1.0.1
   ```

4. **Создайте Release на GitHub**:
   - Перейдите на https://github.com/ВАШ_USERNAME/Chatlist/releases/new
   - Выберите тег: `v1.0.1`
   - Заголовок: `Release v1.0.1`
   - Описание: Используйте шаблон из `RELEASE_NOTES_TEMPLATE.md`
   - Прикрепите файл: `installer/Chatlist-Setup-1.0.1.exe`
   - Нажмите "Publish release"

### Способ 2: Автоматический через GitHub Actions

1. **Создайте ветку для изменений**:
   ```bash
   git checkout -b feature/ci-cd
   ```

2. **Добавьте файл `.github/workflows/release.yml`** (уже создан)

3. **Закоммитьте и запушьте**:
   ```bash
   git add .github/
   git commit -m "Add GitHub Actions for automated releases"
   git push origin feature/ci-cd
   ```

4. **Создайте Pull Request и смержите**

5. **Создайте тег для триггера**:
   ```bash
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin v1.0.1
   ```

6. **GitHub Actions автоматически создаст Release**:
   - Соберет инсталлятор
   - Создаст Release с описанием
   - Прикрепит инсталлятор к Release

## Настройка GitHub Pages

### 1. Подготовка HTML-лендинга

1. Файл `docs/index.html` уже создан
2. Добавьте скриншоты приложения в `docs/images/`
3. Обновите информацию о проекте в HTML

### 2. Включение GitHub Pages

1. Перейдите в Settings → Pages репозитория
2. Source: Deploy from a branch
3. Branch: `main` или `gh-pages`
4. Folder: `/docs`
5. Save

### 3. Доступ к сайту

После включения сайт будет доступен по адресу:
`https://ВАШ_USERNAME.github.io/Chatlist/`

## Структура Release

### Формат имени файла инсталлятора
```
Chatlist-Setup-{версия}.exe
```

Пример: `Chatlist-Setup-1.0.1.exe`

### Описание Release должно включать:

1. **Основные изменения** (Features)
2. **Исправления багов** (Bug Fixes)
3. **Известные проблемы** (Known Issues)
4. **Системные требования**:
   - Windows 10/11 (64-bit)
   - 50 MB свободного места
   - Интернет-соединение для работы с API

## Чек-лист перед Release

- [ ] Версия обновлена в `version.py`
- [ ] Версия обновлена в `setup.iss`
- [ ] Инсталлятор успешно собран
- [ ] Инсталлятор протестирован на чистой системе
- [ ] README.md обновлен
- [ ] CHANGELOG.md обновлен (если используется)
- [ ] Тег версии создан
- [ ] Release notes подготовлены
- [ ] Скриншоты добавлены (для GitHub Pages)

## Автоматизация через GitHub Actions

См. файл `.github/workflows/release.yml` для автоматической сборки и публикации.

При создании тега вида `v*.*.*` (например, `v1.0.1`):
- Автоматически собирается инсталлятор
- Создается Release с описанием из шаблона
- Инсталлятор прикрепляется к Release
