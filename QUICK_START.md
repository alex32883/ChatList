# Быстрый старт: Публикация на GitHub

## 📋 Чек-лист перед публикацией

- [ ] Обновите `YOUR_USERNAME` в файлах (поиск и замена)
- [ ] Добавьте скриншоты в `docs/images/`
- [ ] Проверьте все ссылки на GitHub
- [ ] Убедитесь, что `.gitignore` настроен правильно

## 🚀 Пошаговая инструкция

### Шаг 1: Подготовка репозитория

```bash
# Инициализация Git (если еще не сделано)
git init
git add .
git commit -m "Initial commit"
git branch -M main

# Добавление remote
git remote add origin https://github.com/YOUR_USERNAME/Chatlist.git
git push -u origin main
```

### Шаг 2: Создание первого Release (ручной способ)

1. **Обновите версию**:
   ```bash
   # Отредактируйте version.py
   __version__ = "1.0.1"
   ```

2. **Соберите инсталлятор**:
   ```bash
   build_installer.bat
   ```

3. **Закоммитьте изменения**:
   ```bash
   git add version.py setup.iss
   git commit -m "Bump version to 1.0.1"
   git push origin main
   ```

4. **Создайте тег**:
   ```bash
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin v1.0.1
   ```

5. **Создайте Release на GitHub**:
   - Перейдите на https://github.com/YOUR_USERNAME/Chatlist/releases/new
   - Выберите тег: `v1.0.1`
   - Заголовок: `Release v1.0.1`
   - Скопируйте описание из `RELEASE_NOTES_TEMPLATE.md` и заполните
   - Загрузите файл: `installer/Chatlist-Setup-1.0.1.exe`
   - Нажмите "Publish release"

### Шаг 3: Настройка GitHub Pages

1. **Включите GitHub Pages**:
   - Settings → Pages
   - Source: `main` branch
   - Folder: `/docs`
   - Save

2. **Подождите несколько минут** и откройте:
   - `https://YOUR_USERNAME.github.io/Chatlist/`

### Шаг 4: Автоматизация (опционально)

GitHub Actions уже настроен в `.github/workflows/release.yml`.

При создании тега вида `v*.*.*` автоматически:
- Соберется инсталлятор
- Создастся Release
- Прикрепится инсталлятор

## 📝 Обновление информации

### Заменить YOUR_USERNAME

В следующих файлах замените `YOUR_USERNAME` на ваш GitHub username:
- `docs/index.html`
- `README.md`
- `CHANGELOG.md`
- `RELEASE_NOTES_TEMPLATE.md`
- `.github/workflows/release.yml`

### Добавить скриншоты

1. Создайте папку `docs/images/`
2. Добавьте скриншоты:
   - `screenshot1.png` - главное окно
   - `screenshot2.png` - результаты
   - `screenshot3.png` - управление моделями

## 🔗 Полезные ссылки

- [Подробная инструкция по Release](GITHUB_RELEASE_GUIDE.md)
- [Настройка GitHub Pages](GITHUB_PAGES_SETUP.md)
- [Шаблон Release Notes](RELEASE_NOTES_TEMPLATE.md)

## ❓ Проблемы?

Если что-то не работает:
1. Проверьте, что все файлы закоммичены
2. Убедитесь, что тег создан правильно: `v1.0.1` (не `1.0.1`)
3. Проверьте логи GitHub Actions (Actions tab)
4. Убедитесь, что GitHub Pages включен в Settings
