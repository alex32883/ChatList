@echo off
echo Building installer with Inno Setup...

REM Получаем версию из version.py
python -c "from version import __version__; print(__version__)" > temp_version.txt
set /p VERSION=<temp_version.txt
del temp_version.txt

echo Version: %VERSION%

REM Обновляем версию в setup.iss используя Python
python -c "import re, sys; version = sys.argv[1]; content = open('setup.iss', 'r', encoding='utf-8').read(); content = re.sub(r'#define AppVersion \"[^\"]*\"', f'#define AppVersion \"{version}\"', content); open('setup.iss', 'w', encoding='utf-8').write(content)" %VERSION%

REM Проверяем наличие Inno Setup Compiler
set INNO_SETUP="C:\Users\EPETALE\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not exist %INNO_SETUP% (
    set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)
if not exist %INNO_SETUP% (
    set INNO_SETUP="C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not exist %INNO_SETUP% (
    echo Error: Inno Setup Compiler not found!
    echo Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
    echo Or specify the path to ISCC.exe in this script.
    pause
    exit /b 1
)

REM Компилируем инсталлятор
%INNO_SETUP% setup.iss

echo.
echo Installer build complete! Check the 'installer' folder.
pause
