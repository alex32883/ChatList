# Настройка GitHub Pages

## Быстрый старт

1. **Убедитесь, что файлы готовы**:
   - `docs/index.html` - главная страница лендинга
   - `docs/.nojekyll` - отключает Jekyll обработку
   - (Опционально) `docs/images/` - папка со скриншотами

2. **Включите GitHub Pages**:
   - Перейдите в Settings → Pages вашего репозитория
   - Source: Deploy from a branch
   - Branch: `main` (или `gh-pages`)
   - Folder: `/docs`
   - Save

3. **Доступ к сайту**:
   - Ваш сайт будет доступен по адресу:
   - `https://ВАШ_USERNAME.github.io/Chatlist/`
   - Или `https://ВАШ_USERNAME.github.io/Chatlist/index.html`

## Настройка кастомного домена (опционально)

1. В Settings → Pages добавьте ваш домен
2. Создайте файл `docs/CNAME` с вашим доменом
3. Настройте DNS записи у вашего провайдера

## Обновление лендинга

После каждого изменения в файлах `docs/index.html`:
1. Закоммитьте изменения:
   ```bash
   git add docs/
   git commit -m "Update landing page"
   git push origin main
   ```
2. GitHub Pages автоматически обновится в течение нескольких минут

## Добавление скриншотов

1. Создайте папку `docs/images/`:
   ```bash
   mkdir docs/images
   ```

2. Добавьте скриншоты приложения:
   - `screenshot1.png` - главное окно
   - `screenshot2.png` - результаты сравнения
   - `screenshot3.png` - управление моделями

3. Обновите пути в `docs/index.html` при необходимости

## Персонализация лендинга

В файле `docs/index.html` замените:
- `YOUR_USERNAME` на ваш GitHub username
- `YOUR_REPO_NAME` на имя вашего репозитория
- Обновите описание, возможности и другую информацию

## Структура файлов

```
docs/
├── .nojekyll          # Отключает Jekyll
├── index.html         # Главная страница
└── images/            # Скриншоты (создайте вручную)
    ├── screenshot1.png
    ├── screenshot2.png
    └── screenshot3.png
```
