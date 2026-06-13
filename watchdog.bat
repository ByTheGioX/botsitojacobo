@echo off
:: ============================================================
::  WATCHDOG - Verifica si el bot esta vivo
::
::  - Lee el log mas reciente de data\log\YYYY-MM-DD.log
::  - Si fue modificado hace mas de 30 minutos -> bot dormido
::  - Si no existe el log de hoy -> bot nunca arranco
::  - En ambos casos arranca run_modo_continuo.bat
::
::  Recomendado: Task Scheduler cada 30 minutos como BACKUP.
::  No reemplaza al modo continuo; solo lo resucita si muere.
:: ============================================================

cd /d "%~dp0"
setlocal enableextensions

:: Horario operativo: 10:00 - 23:00. Fuera de ese rango no rescatamos.
for /f %%h in ('powershell -NoProfile -Command "(Get-Date).Hour"') do set CUR_HOUR=%%h
if %CUR_HOUR% LSS 10 (
    echo [watchdog] Fuera de horario operativo ^(%CUR_HOUR%h ^< 10^). No se actua.
    exit /b 0
)
if %CUR_HOUR% GEQ 23 (
    echo [watchdog] Fuera de horario operativo ^(%CUR_HOUR%h ^>= 23^). No se actua.
    exit /b 0
)

set LOG_DIR=%~dp0data\log
set MAX_AGE_MIN=30

:: Obtener fecha de hoy en formato YYYY-MM-DD via PowerShell
for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%a
set TODAY_LOG=%LOG_DIR%\%TODAY%.log

echo [%date% %time%] [watchdog] verificando %TODAY_LOG%

if not exist "%TODAY_LOG%" (
    echo [watchdog] No hay log de hoy. Bot no ha corrido. Arrancando...
    goto RESCUE
)

:: Edad del log en minutos (PowerShell devuelve un entero por exit)
powershell -NoProfile -Command "if (((Get-Date) - (Get-Item '%TODAY_LOG%').LastWriteTime).TotalMinutes -gt %MAX_AGE_MIN%) { exit 1 } else { exit 0 }"
if errorlevel 1 (
    echo [watchdog] Log no actualizado en %MAX_AGE_MIN%+ minutos. Bot dormido. Reiniciando...
    goto RESCUE
)

echo [watchdog] Bot vivo - log actualizado recientemente. OK.
endlocal
exit /b 0

:RESCUE
:: Mata instancias zombis antes de reiniciar
taskkill /f /im python.exe        2>nul
taskkill /f /im chrome.exe        2>nul
taskkill /f /im chromedriver.exe  2>nul
timeout /t 3 /nobreak >nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonLock"   2>nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonSocket" 2>nul
del /f /q "%USERPROFILE%\Desktop\browser_cache\SingletonCookie" 2>nul

:: Lanzar modo continuo en ventana minimizada (no bloqueante)
start "BotParaparkContinuo" /min cmd /c "%~dp0run_modo_continuo.bat"

echo [watchdog] Modo continuo lanzado en ventana aparte.
endlocal
exit /b 0
