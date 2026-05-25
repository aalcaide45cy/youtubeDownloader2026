@echo off
title YT Downloader Premium - Servidor Local
echo ===================================================
echo   INICIANDO YT DOWNLOADER PREMIUM (SERVIDOR LOCAL)
echo ===================================================
echo.

:: Comprobar si existe el entorno virtual .venv
if not exist .venv (
    echo [INFO] Creando el entorno virtual .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual. Asegurate de tener Python instalado y en tu PATH.
        pause
        exit /b 1
    )
)

:: Activar entorno virtual e instalar dependencias
echo [INFO] Verificando e instalando dependencias necesarias...
call .venv\Scripts\activate
python -m pip install fastapi uvicorn yt-dlp
if errorlevel 1 (
    echo [ERROR] No se pudieron instalar las dependencias de Python.
    pause
    exit /b 1
)

echo.
echo [INFO] Iniciando el servidor FastAPI en http://127.0.0.1:8000...
echo [INFO] La interfaz se abrira automaticamente en tu navegador.
echo [INFO] Para detener el servidor, cierra esta ventana o presiona CTRL+C.
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [WARN] El servidor se ha detenido.
    pause
)
