@echo off
setlocal

:: ============================================================
::  CICLO COMPLETO - Bot Principal + Bot Fotos
::  Ejecuta ambos bots en secuencia sin que choquen.
::  Recomendado: programar en Task Scheduler cada 30 minutos.
:: ============================================================

set BOT_PRINCIPAL=C:\Users\Turitop\Desktop\Booking_bot\bot
set BOT_FOTOS=C:\Users\Turitop\Desktop\bot\bot

echo.
echo ============================================================
echo   CICLO COMPLETO [%date% %time%]
echo ============================================================

:: --- Limpieza inicial: matar cualquier proceso previo ---
echo.
echo [1/4] Limpiando procesos anteriores...
taskkill /f /im chrome.exe        2>nul
taskkill /f /im chromedriver.exe  2>nul
taskkill /f /im python.exe        2>nul
timeout /t 3 /nobreak >nul

:: --- Bot Principal ---
echo.
echo [2/4] Iniciando Bot Principal (reservas y notificaciones)...
echo       Ruta: %BOT_PRINCIPAL%
echo       Hora inicio: %time%
cd /d "%BOT_PRINCIPAL%"
python booking_notifier_ts.py
echo       Hora fin:    %time%
echo       Codigo de salida: %errorlevel%

:: --- Limpieza entre bots ---
echo.
echo [3/4] Limpiando Chrome entre bots...
taskkill /f /im chrome.exe        2>nul
taskkill /f /im chromedriver.exe  2>nul
timeout /t 5 /nobreak >nul

:: --- Bot Fotos ---
echo.
echo [4/4] Iniciando Bot Fotos (fotos, reviews, respuestas)...
echo       Ruta: %BOT_FOTOS%
echo       Hora inicio: %time%
cd /d "%BOT_FOTOS%"
python test_photo_modules.py --auto
echo       Hora fin:    %time%
echo       Codigo de salida: %errorlevel%

:: --- Limpieza final ---
taskkill /f /im chrome.exe        2>nul
taskkill /f /im chromedriver.exe  2>nul

echo.
echo ============================================================
echo   CICLO COMPLETADO [%date% %time%]
echo ============================================================
echo.
