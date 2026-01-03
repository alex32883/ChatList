@echo off
echo Building Windows executable...
pyinstaller --onefile --windowed --name "PyQtApp" main.py
echo.
echo Build complete! Executable is in the 'dist' folder.
pause


