# Исправление ошибки GitHub Pages

## Проблема
```
Error: No artifacts named "github-pages" were found for this workflow run.
```

## Решение

Создан новый workflow файл `.github/workflows/pages.yml` для деплоя на GitHub Pages.

## Что нужно сделать

### 1. Проверьте настройки GitHub Pages

1. Перейдите в **Settings** → **Pages** вашего репозитория
2. **Source**: выберите **"GitHub Actions"** (не "Deploy from a branch")
3. Сохраните настройки

### 2. Файлы уже созданы

- ✅ `.github/workflows/pages.yml` - workflow для деплоя
- ✅ `docs/index.html` - лендинг страница
- ✅ `docs/.nojekyll` - отключает Jekyll

### 3. Запуск деплоя

Workflow автоматически запустится при:
- Push в ветку `main`
- Изменении файлов в папке `docs/`
- Ручном запуске через **Actions** → **Deploy to GitHub Pages** → **Run workflow**

### 4. Проверка работы

После успешного деплоя:
- Сайт будет доступен по адресу: `https://YOUR_USERNAME.github.io/Chatlist/`
- Статус деплоя можно проверить во вкладке **Actions**

## Если проблема остается

1. **Проверьте логи** в разделе **Actions**
2. **Убедитесь**, что в Settings → Pages выбран **"GitHub Actions"** как источник
3. **Проверьте**, что файл `.github/workflows/pages.yml` существует и правильно настроен
4. **Убедитесь**, что у workflow есть необходимые permissions (они указаны в файле)

## Альтернативный способ (если GitHub Actions не работает)

Если по каким-то причинам GitHub Actions не работает, можно использовать деплой из branch:

1. Settings → Pages
2. Source: **"Deploy from a branch"**
3. Branch: `main` или `gh-pages`
4. Folder: `/docs`

Но в этом случае нужно либо:
- Создать отдельную ветку `gh-pages` и пушить туда файлы из `docs/`
- Или использовать другой workflow для автоматизации

Рекомендуется использовать **GitHub Actions** (способ выше), так как он автоматизирован и более гибкий.
