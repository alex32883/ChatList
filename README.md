# PyQt Application

Минимальная программа на Python с графическим интерфейсом на PyQt5.

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Запуск программы

```bash
python main.py
```

## Создание Windows исполняемого файла

Для создания исполняемого файла (.exe) используйте:

```bash
build_exe.bat
```

Или вручную:

```bash
pyinstaller --onefile --windowed --name "PyQtApp" main.py
```

Исполняемый файл будет находиться в папке `dist`.

## Описание

Программа создает окно с кнопкой "Click on me". При нажатии на кнопку отображается сообщение "Минимальная программа на Python".

