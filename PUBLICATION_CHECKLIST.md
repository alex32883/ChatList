# Чек-лист публикации на GitHub

## ✅ Перед первым релизом

### 1. Настройка проекта
- [ ] Создан репозиторий на GitHub
- [ ] `.gitignore` настроен правильно
- [ ] Все файлы добавлены в Git
- [ ] Первый коммит сделан и запушен

### 2. Персонализация
- [ ] Заменен `YOUR_USERNAME` на ваш GitHub username во всех файлах:
  - `docs/index.html`
  - `README.md`
  - `CHANGELOG.md`
  - `RELEASE_NOTES_TEMPLATE.md`
  - `.github/workflows/release.yml`

- [ ] Заменен `YOUR_REPO_NAME` (если отличается от `Chatlist`)

### 3. Подготовка контента
- [ ] Добавлены скриншоты в `docs/images/`:
  - `screenshot1.png` - главное окно
  - `screenshot2.png` - результаты сравнения
  - `screenshot3.png` - управление моделями

- [ ] Обновлена информация о проекте в `docs/index.html`
- [ ] Обновлен `README.md` с актуальной информацией
- [ ] Обновлен `CHANGELOG.md` для первой версии

### 4. Тестирование
- [ ] Инсталлятор протестирован на чистой системе
- [ ] Приложение запускается после установки
- [ ] Все функции работают корректно

## 🚀 Перед каждым релизом

### 1. Обновление версии
- [ ] Версия обновлена в `version.py`
- [ ] Версия обновлена в `setup.iss` (автоматически через `build_installer.bat`)
- [ ] Версия обновлена в `CHANGELOG.md`
- [ ] Версия обновлена в `README.md` (если нужно)

### 2. Сборка
- [ ] Инсталлятор успешно собран: `build_installer.bat`
- [ ] Исполняемый файл собран: `build_exe.bat` или через spec
- [ ] Инсталлятор находится в папке `installer/`

### 3. Подготовка Release Notes
- [ ] Используется шаблон из `RELEASE_NOTES_TEMPLATE.md`
- [ ] Заполнены все разделы:
  - Новые возможности
  - Исправления багов
  - Улучшения
- [ ] Обновлены ссылки на версию

### 4. Создание Release

#### Вариант A: Ручной способ
- [ ] Изменения закоммичены и запушены
- [ ] Создан тег: `git tag -a v1.0.1 -m "Release version 1.0.1"`
- [ ] Тег запушен: `git push origin v1.0.1`
- [ ] Release создан на GitHub
- [ ] Инсталлятор прикреплен к Release

#### Вариант B: Автоматический (через GitHub Actions)
- [ ] GitHub Actions настроен (`.github/workflows/release.yml`)
- [ ] Создан тег: `git tag -a v1.0.1 -m "Release version 1.0.1"`
- [ ] Тег запушен: `git push origin v1.0.1`
- [ ] Проверены логи GitHub Actions
- [ ] Release автоматически создан

### 5. Обновление GitHub Pages
- [ ] GitHub Pages включен в Settings
- [ ] Источник: `main` branch, папка `/docs`
- [ ] Сайт доступен по адресу: `https://YOUR_USERNAME.github.io/Chatlist/`
- [ ] Лендинг обновлен с новой версией (если нужно)

## 📝 Структура файлов для публикации

```
Chatlist/
├── .github/
│   └── workflows/
│       └── release.yml          # GitHub Actions для автоматической сборки
├── docs/
│   ├── .nojekyll                # Отключает Jekyll
│   ├── index.html               # Лендинг для GitHub Pages
│   └── images/                  # Скриншоты (создайте вручную)
│       ├── screenshot1.png
│       ├── screenshot2.png
│       └── screenshot3.png
├── installer/
│   └── Chatlist-Setup-X.X.X.exe # Инсталлятор (после сборки)
├── dist/
│   └── PyQtApp.exe              # Исполняемый файл (после сборки)
├── version.py                   # Версия приложения
├── setup.iss                    # Скрипт Inno Setup
├── CHANGELOG.md                 # История изменений
├── RELEASE_NOTES_TEMPLATE.md    # Шаблон для Release Notes
├── GITHUB_RELEASE_GUIDE.md      # Подробная инструкция
├── GITHUB_PAGES_SETUP.md        # Инструкция по GitHub Pages
├── QUICK_START.md               # Быстрый старт
└── README.md                    # Основной README
```

## 🔗 Полезные команды

### Сборка инсталлятора
```bash
build_installer.bat
```

### Создание тега и Release
```bash
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin v1.0.1
```

### Обновление GitHub Pages
```bash
git add docs/
git commit -m "Update landing page"
git push origin main
```

## ❓ Часто возникающие проблемы

### Инсталлятор не прикрепляется к Release
- Убедитесь, что файл находится в папке `installer/`
- Проверьте размер файла (не должен превышать 100 MB)

### GitHub Pages не обновляется
- Проверьте настройки в Settings → Pages
- Убедитесь, что файл `docs/.nojekyll` присутствует
- Подождите несколько минут (обновление не мгновенное)

### GitHub Actions не работает
- Проверьте логи в разделе Actions
- Убедитесь, что файл `.github/workflows/release.yml` существует
- Проверьте синтаксис YAML файла

### Тег не триггерит Release
- Убедитесь, что тег имеет формат `v*.*.*` (например, `v1.0.1`)
- Проверьте, что тег запушен: `git push origin v1.0.1`

## 📚 Дополнительные ресурсы

- [Подробная инструкция по Release](GITHUB_RELEASE_GUIDE.md)
- [Настройка GitHub Pages](GITHUB_PAGES_SETUP.md)
- [Быстрый старт](QUICK_START.md)
