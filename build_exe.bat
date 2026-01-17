@echo off
echo Building Windows executable...

REM Получаем версию из version.py
python -c "from version import __version__; print(__version__)" > temp_version.txt
set /p VERSION=<temp_version.txt
del temp_version.txt

echo Version: %VERSION%

if exist app.ico (
    echo Icon found: app.ico
    python -m PyInstaller --onefile --windowed --name "PyQtApp-%VERSION%" --icon=app.ico main.py
) else (
    echo Warning: app.ico not found, building without icon
    python -m PyInstaller --onefile --windowed --name "PyQtApp-%VERSION%" main.py
)
echo.
echo Build complete! Executable is in the 'dist' folder.
pause




