@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "backend" (
    echo [ОШИБКА] Папка backend не найдена!
    pause
    exit /b
)

cd backend

python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    pause
    exit /b
)

echo ======================================
echo   OSINT Phone Hunter Pro
echo ======================================
echo.
echo [*] Запуск сервера...
start "" /B python main.py

echo [*] Ожидание сервера...
timeout /t 3 /nobreak >nul

set "HTML_FILE=%~dp0frontend\index.html"

echo [*] HTML: %HTML_FILE%

echo [*] Поиск Firefox...
set "FF="
if exist "C:\Program Files\Mozilla Firefox\firefox.exe" set "FF=C:\Program Files\Mozilla Firefox\firefox.exe"
if exist "C:\Program Files (x86)\Mozilla Firefox\firefox.exe" set "FF=C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
if exist "%LOCALAPPDATA%\Mozilla Firefox\firefox.exe" set "FF=%LOCALAPPDATA%\Mozilla Firefox\firefox.exe"

if defined FF (
    echo [*] Firefox найден: %FF%
    start "" "%FF%" "file:///%HTML_FILE:\=/%"
) else (
    echo [!] Firefox не найден, пробую браузер по умолчанию...
    start "" "%HTML_FILE%"
)

echo.
echo Сервер: http://127.0.0.1:8000
echo Закройте это окно чтобы остановить сервер.
pause >nul