@echo off
:: ============================================================
::  MODO CONTINUO - Bot Parapark
::
::  Python corre en bucle interno (while True) y mantiene el
::  navegador abierto entre ciclos -> WhatsApp Web no se desvincula.
::
::  Este .bat solo relanza Python si crashea (resiliencia).
::  Tambien gestiona limpieza de Chrome/locks entre crashes.
::
::  Recomendado: ejecutar al INICIAR Windows (autoarranque).
::  Para autoarranque manual:
::    1. Pulsa Win + R
::    2. Escribe:  shell:startup
::    3. Crea un acceso directo de este .bat en esa carpeta
::
::  Para parar el bot: cierra la ventana (Ctrl+C reinicia el bot).
:: ============================================================

cd /d "%~dp0"
title BotParaparkContinuo

echo.
echo ============================================================
echo   MODO CONTINUO - Bot Parapark
echo   PID padre: %ERRORLEVEL%
echo   Carpeta:   %~dp0
echo ============================================================
echo.

:: --- Limpieza inicial: matar instancias previas ---
echo [INIT] Limpiando procesos anteriores...
taskkill /f /im python.exe        2>nul
taskkill /f /im chrome.exe        2>nul
taskkill /f /im chromedriver.exe  2>nul
timeout /t 3 /nobreak >nul

:: Limpiar locks del cache de Chrome (causan "perfil en uso")
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonLock"   2>nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonSocket" 2>nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonCookie" 2>nul

set RESTART_COUNT=0

:LOOP
set /a RESTART_COUNT+=1
echo.
echo ============================================================
echo   Arranque #%RESTART_COUNT% del bot [%date% %time%]
echo ============================================================
echo.

:: Lanza el bot y espera a que termine
python test_photo_modules.py --auto

echo.
echo ============================================================
echo   Bot detenido [%date% %time%]
echo   ExitCode: %ERRORLEVEL% ^| Reinicio #%RESTART_COUNT%
echo ============================================================

:: Limpieza por seguridad antes del proximo intento
taskkill /f /im chrome.exe        2>nul
taskkill /f /im chromedriver.exe  2>nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonLock"   2>nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonSocket" 2>nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonCookie" 2>nul

:: Si estamos fuera de horario operativo (10-23h), esperar 5 min antes de reintentar
for /f %%h in ('powershell -NoProfile -Command "(Get-Date).Hour"') do set CUR_HOUR=%%h
if %CUR_HOUR% LSS 10 (
    echo Fuera de horario. Esperando 5 minutos...
    timeout /t 300 /nobreak >nul
    goto LOOP
)
if %CUR_HOUR% GEQ 23 (
    echo Fuera de horario. Esperando 5 minutos...
    timeout /t 300 /nobreak >nul
    goto LOOP
)

echo Esperando 30 segundos antes de reiniciar...
echo (Pulsa Ctrl+C ahora si quieres detener el bucle.)
timeout /t 30

goto LOOP
