@echo off
echo Building Windows executable...
if exist app.ico (
    echo Icon found: app.ico
    python -m PyInstaller --onefile --windowed --name "PyQtApp" --icon=app.ico main.py
) else (
    echo Warning: app.ico not found, building without icon
    python -m PyInstaller --onefile --windowed --name "PyQtApp" main.py
)
echo.
echo Build complete! Executable is in the 'dist' folder.
pause




