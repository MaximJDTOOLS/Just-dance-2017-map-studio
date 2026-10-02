@echo off
REM ============================================================
REM  JD2017 Tool - Build EXE
REM  Полная сборка: venv + зависимости + PyInstaller
REM ============================================================

setlocal EnableDelayedExpansion
chcp 65001 >nul
title JD2017 Tool - Build

REM --- Настройки ---
set APP_NAME=JD2017Tool
set ENTRY=main.py
set VENV_DIR=.venv
set DIST_DIR=dist
set BUILD_DIR=build

echo.
echo ============================================================
echo   JD2017 Tool  -  Сборка EXE
echo ============================================================
echo.

REM --- Проверка Python ---
echo [1/6] Проверка Python...
where python >nul 2>nul
if errorlevel 1 (
    echo [ОШИБКА] Python не найден в PATH.
    echo Установите Python 3.10+ с https://www.python.org/downloads/
    echo и обязательно отметьте "Add Python to PATH".
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo       Python версия: !PYVER!
echo.

REM --- Создание виртуального окружения ---
echo [2/6] Виртуальное окружение (!VENV_DIR!)...
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo       Уже существует, пропускаем создание.
) else (
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать venv.
        pause
        exit /b 1
    )
    echo       Создано.
)
echo.

REM --- Активация ---
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ОШИБКА] Не удалось активировать venv.
    pause
    exit /b 1
)

REM --- Установка зависимостей ---
echo [3/6] Установка зависимостей...
python -m pip install --upgrade pip --quiet
if exist "requirements.txt" (
    pip install -r requirements.txt --quiet
) else (
    pip install PyQt6 Pillow pyinstaller --quiet
)
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости.
    pause
    exit /b 1
)
echo       Зависимости установлены.
echo.

REM --- Очистка старых сборок ---
echo [4/6] Очистка старых артефактов...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%"  rmdir /s /q "%DIST_DIR%"
if exist "__pycache__"  rmdir /s /q "__pycache__"
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
echo       Готово.
echo.

REM --- PyInstaller ---
echo [5/6] Сборка через PyInstaller...
echo.

REM Проверяем наличие .spec файла
if exist "jd2017_tool.spec" (
    pyinstaller --clean --noconfirm "jd2017_tool.spec"
) else (
    echo       .spec не найден, собираем в режиме onedir с оптимизациями...
    pyinstaller ^
        --name "%APP_NAME%" ^
        --windowed ^
        --noconfirm ^
        --clean ^
        --onedir ^
        --collect-all PyQt6 ^
        --hidden-import PyQt6.QtCore ^
        --hidden-import PyQt6.QtGui ^
        --hidden-import PyQt6.QtWidgets ^
        --hidden-import PIL ^
        --hidden-import PIL.Image ^
        --hidden-import PIL.ImageQt ^
        --hidden-import PIL.ImageDraw ^
        --exclude-module tkinter ^
        --exclude-module matplotlib ^
        --exclude-module numpy ^
        --exclude-module scipy ^
        --exclude-module pandas ^
        --exclude-module pytest ^
        --noupx ^
        "%ENTRY%"
)

if errorlevel 1 (
    echo.
    echo [ОШИБКА] PyInstaller завершился с ошибкой.
    pause
    exit /b 1
)

echo.
echo [6/6] Копирование вспомогательных файлов...

REM Копируем README, если есть
if exist "README.md" copy /y "README.md" "%DIST_DIR%\%APP_NAME%\" >nul

REM Копируем папку assets, если есть
if exist "assets" (
    if not exist "%DIST_DIR%\%APP_NAME%\assets" mkdir "%DIST_DIR%\%APP_NAME%\assets"
    xcopy /e /i /y "assets\*" "%DIST_DIR%\%APP_NAME%\assets\" >nul
)

echo.
echo ============================================================
echo   ГОТОВО!
echo ============================================================
echo.
echo   Исполняемый файл:
echo     %DIST_DIR%\%APP_NAME%\%APP_NAME%.exe
echo.
echo   Для распространения упакуйте папку:
echo     %DIST_DIR%\%APP_NAME%\
echo.

REM --- Предложение создать ZIP ---
choice /M "Создать ZIP-архив для распространения"
if errorlevel 2 goto :skip_zip
if errorlevel 1 (
    echo Создание ZIP...
    powershell -NoProfile -Command ^
        "Compress-Archive -Path '%DIST_DIR%\%APP_NAME%\*' -DestinationPath '%DIST_DIR%\%APP_NAME%.zip' -Force"
    echo ZIP создан: %DIST_DIR%\%APP_NAME%.zip
)

:skip_zip
echo.
echo Нажмите любую клавишу для выхода...
pause >nul
endlocal
exit /b 0