@echo off
setlocal

:: ============================================================
::  CICLO COMPLETO - Bot Fotos + Bot Principal
::  Ejecuta ambos bots en secuencia sin que choquen.
::  El Bot Principal corre UN solo ciclo (hasta "waiting for 15
::  minutes") y luego se cierra automaticamente.
::  Recomendado: programar en Task Scheduler cada 30 minutos.
:: ============================================================

set BOT_FOTOS=C:\Users\Turitop\Desktop\bot
set BOT_PRINCIPAL=C:\Users\Turitop\Desktop\Booking_bot\bot
set BOT_LOG=%TEMP%\bot_principal_output.log

echo.
echo ============================================================
echo   CICLO COMPLETO [%date% %time%]
echo ============================================================

:: --- Limpieza inicial ---
echo.
echo [1/5] Limpiando procesos anteriores...
taskkill /f /im python.exe        2>nul
taskkill /f /im chrome.exe        2>nul
taskkill /f /im chromedriver.exe  2>nul
timeout /t 3 /nobreak >nul

:: --- Bot Fotos (primero) ---
echo.
echo [2/5] Iniciando Bot Fotos (fotos, reviews, respuestas)...
echo       Ruta: %BOT_FOTOS%
echo       Hora inicio: %time%
start /wait "Bot Fotos" cmd /c "cd /d "%BOT_FOTOS%" && python test_photo_modules.py --auto"
echo       Hora fin:    %time%

:: --- Limpieza entre bots ---
echo.
echo [3/5] Limpiando Chrome entre bots...
taskkill /f /im chrome.exe        2>nul
taskkill /f /im chromedriver.exe  2>nul
timeout /t 3 /nobreak >nul
:: Limpiar lock files del perfil Chrome
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonLock" 2>nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonSocket" 2>nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonCookie" 2>nul
timeout /t 2 /nobreak >nul

:: --- Bot Principal (un solo ciclo) ---
echo.
echo [4/5] Iniciando Bot Principal (un solo ciclo)...
echo       Ruta: %BOT_PRINCIPAL%
echo       Hora inicio: %time%

:: Limpiar log anterior
del /f /q "%BOT_LOG%" 2>nul

:: Iniciar bot principal en background con salida a log (-u = unbuffered)
start "Bot Principal" /B cmd /c "cd /d "%BOT_PRINCIPAL%" && python -u booking_notifier_keep_browser_opened.py > "%BOT_LOG%" 2>&1"

:: Esperar a que complete un ciclo (detectar "waiting for 15 minutes" o error de login)
echo       Esperando a que complete un ciclo...
set MAX_WAIT=120
set WAITED=0

:WAIT_CYCLE
timeout /t 10 /nobreak >nul
set /a WAITED+=10

:: Verificar si completo un ciclo
findstr /i /c:"waiting for 15 minutes" "%BOT_LOG%" >nul 2>&1
if %errorlevel%==0 (
    echo       Bot Principal completo un ciclo exitosamente.
    goto CYCLE_DONE
)

:: Verificar si se deslogueo (error fatal)
findstr /i /c:"please login and press enter" "%BOT_LOG%" >nul 2>&1
if %errorlevel%==0 (
    echo       Bot Principal perdio la sesion - cerrando.
    goto CYCLE_DONE
)

:: Verificar timeout (20 minutos maximo)
if %WAITED% GEQ %MAX_WAIT% (
    echo       Timeout de %MAX_WAIT%0 segundos alcanzado - cerrando.
    goto CYCLE_DONE
)

goto WAIT_CYCLE

:CYCLE_DONE
echo       Hora fin:    %time%

:: --- Limpieza final ---
echo.
echo [5/5] Limpieza final...
taskkill /f /im python.exe        2>nul
taskkill /f /im chrome.exe        2>nul
taskkill /f /im chromedriver.exe  2>nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonLock" 2>nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonSocket" 2>nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonCookie" 2>nul

echo.
echo ============================================================
echo   CICLO COMPLETADO [%date% %time%]
echo ============================================================
echo.
