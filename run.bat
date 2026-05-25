@echo off
title YT Downloader Premium - Servidor Local
echo ===================================================
echo   INICIANDO YT DOWNLOADER PREMIUM (SERVIDOR LOCAL)
echo ===================================================
echo.

:: 1. Comprobar si FFmpeg está instalado en el sistema
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo [AVISO] FFmpeg no esta instalado o no se encuentra en el PATH.
    echo FFmpeg es necesario para fusionar videos en alta calidad (1080p, 4K) y audios.
    echo.
    set /p CHOICE="No tienes FFmpeg instalado en el equipo, ¿quieres que lo instale automaticamente? (S/N): "
    
    if /i "%CHOICE%"=="S" (
        echo.
        echo [INFO] Intentando instalar FFmpeg usando Winget (Windows Package Manager)...
        echo Esto puede tardar unos minutos, por favor espera...
        echo.
        
        winget install --id Gyan.FFmpeg --exact --silent --accept-source-agreements --accept-package-agreements
        
        if %errorlevel% equ 0 (
            echo.
            echo =======================================================================
            echo   [EXITO] FFmpeg se ha instalado correctamente de manera automatica.
            echo   [IMPORTANTE] Para que los cambios surtan efecto y se registre en la
            echo   consola, por favor CIERRA ESTA VENTANA y vuelve a ejecutar 'run.bat'.
            echo =======================================================================
            echo.
            pause
            exit /b 0
        ) else (
            echo.
            echo [ERROR] No se pudo instalar FFmpeg automaticamente.
            echo Posibles razones:
            echo - No tienes conexion a Internet o Winget no esta disponible.
            echo - Windows SmartScreen o permisos de administrador detuvieron la instalacion.
            echo.
            echo Puedes instalarlo manualmente descargandolo desde: https://ffmpeg.org/
            echo.
            pause
        )
    ) else (
        echo.
        echo [ADVERTENCIA] Has decidido no instalar FFmpeg.
        echo Nota: Las descargas de video en resoluciones altas podrian fallar o descargarse sin audio.
        echo.
        pause
    )
)

:: 2. Comprobar si existe el entorno virtual .venv
if not exist .venv (
    echo [INFO] Creando el entorno virtual .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual. Asegurate de tener Python instalado y en tu PATH.
        pause
        exit /b 1
    )
)

:: 3. Activar entorno virtual e instalar dependencias
echo [INFO] Verificando e instalar/actualizar dependencias necesarias...
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
