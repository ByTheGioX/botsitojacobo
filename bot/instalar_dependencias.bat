@echo off
cd /d "%~dp0"
echo ============================================
echo   Instalando dependencias del bot...
echo ============================================
echo.

pip install selenium webdriver-manager pyautogui

echo.
echo ============================================
echo   Listo! Ahora ejecuta run_keep_browser_opened.bat
echo ============================================
echo.
pause
