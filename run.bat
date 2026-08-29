@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================
echo   Phone Hunter BETA-1.0
echo   Локальный OSINT инструмент
echo ======================================
echo.

if not exist "backend" (
    echo [ОШИБКА] Папка backend не найдена!
    pause
    exit /b
)

if not exist "frontend" (
    echo [ОШИБКА] Папка frontend не найдена!
    pause
    exit /b
)

cd backend

python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден! Установите Python 3.10+
    echo https://www.python.org/downloads/
    pause
    exit /b
)

echo [*] Проверка зависимостей...
if not exist "requirements.txt" (
    echo [ОШИБКА] requirements.txt не найден!
    pause
    exit /b
)

echo [*] Установка зависимостей...
pip install -r requirements.txt -q

echo.
echo [*] Запуск сервера...
start "" /B python main.py

echo [*] Ожидание запуска сервера...
timeout /t 3 /nobreak >nul

set "HTML_FILE=%~dp0frontend\index.html"

echo [*] Открытие интерфейса...
if exist "C:\Program Files\Mozilla Firefox\firefox.exe" (
    start "" "C:\Program Files\Mozilla Firefox\firefox.exe" "file:///%HTML_FILE:\=/%"
) else if exist "C:\Program Files (x86)\Mozilla Firefox\firefox.exe" (
    start "" "C:\Program Files (x86)\Mozilla Firefox\firefox.exe" "file:///%HTML_FILE:\=/%"
) else (
    echo [*] Firefox не найден, открываю в браузере по умолчанию...
    start "" "%HTML_FILE%"
)

echo.
echo ======================================
echo   Сервер запущен!
echo   API: http://127.0.0.1:8000
echo   Docs: http://127.0.0.1:8000/docs
echo.
echo   Закройте это окно чтобы остановить
echo ======================================
echo.
pause >nul