@echo off
title YT Downloader Premium - Servidor Local
echo ===================================================
echo   INICIANDO YT DOWNLOADER PREMIUM (SERVIDOR LOCAL)
echo ===================================================
echo.

:: 1. Comprobar si FFmpeg esta instalado en el sistema
where ffmpeg >nul 2>nul
if %errorlevel% equ 0 goto ffmpeg_ok

echo [AVISO] FFmpeg no esta instalado o no se encuentra en el PATH.
echo FFmpeg es necesario para fusionar videos en alta calidad y audios.
echo.
set /p CHOICE="No tienes FFmpeg instalado en el equipo. Quieres que lo instale automaticamente? (S/N): "

if /i "%CHOICE%"=="S" goto install_ffmpeg
if /i "%CHOICE%"=="SI" goto install_ffmpeg
goto no_install_ffmpeg

:install_ffmpeg
echo.
echo [INFO] Intentando instalar FFmpeg usando Winget (Windows Package Manager)...
echo Esto puede tardar unos minutos, por favor espera...
echo.

winget install --id Gyan.FFmpeg --exact --silent --accept-source-agreements --accept-package-agreements
if %errorlevel% equ 0 goto winget_success
goto winget_fail

:winget_success
echo.
echo =======================================================================
echo   [EXITO] FFmpeg se ha instalado correctamente.
echo   [IMPORTANTE] Por favor, CIERRA ESTA VENTANA y vuelve a abrir 'run.bat'
echo   para que se aplique la nueva ruta de FFmpeg.
echo =======================================================================
echo.
pause
exit /b 0

:winget_fail
echo.
echo [ERROR] No se pudo instalar FFmpeg automaticamente.
echo Puedes instalarlo manualmente descargandolo desde https://ffmpeg.org/
echo.
pause
goto ffmpeg_ok

:no_install_ffmpeg
echo.
echo [ADVERTENCIA] Has decidido no instalar FFmpeg.
echo Nota: Las descargas de video en resoluciones altas podrian fallar.
echo.
pause
goto ffmpeg_ok

:ffmpeg_ok

:: 2. Comprobar si existe el entorno virtual .venv
if exist .venv goto venv_exists

echo [INFO] Creando el entorno virtual .venv...
python -m venv .venv
if %errorlevel% neq 0 goto venv_error
goto venv_exists

:venv_error
echo.
echo [ERROR] No se pudo crear el entorno virtual. 
echo Asegurate de tener Python instalado y en tu PATH de Windows.
echo.
pause
exit /b 1

:venv_exists

:: 3. Activar entorno virtual e instalar dependencias
echo [INFO] Verificando e instalando/actualizando dependencias necesarias...
call .venv\Scripts\activate
if %errorlevel% neq 0 goto env_activate_error

python -m pip install fastapi uvicorn yt-dlp
if %errorlevel% neq 0 goto pip_error
goto dependencies_ok

:env_activate_error
echo.
echo [ERROR] No se pudo activar el entorno virtual (.venv\Scripts\activate).
echo.
pause
exit /b 1

:pip_error
echo.
echo [ERROR] No se pudieron instalar las dependencias de Python usando pip.
echo.
pause
exit /b 1

:dependencies_ok

echo.
echo [INFO] Iniciando el servidor FastAPI en http://127.0.0.1:8000...
echo [INFO] La interfaz se abrira automaticamente en tu navegador.
echo [INFO] Para detener el servidor, cierra esta ventana o presiona CTRL+C.
echo.

python main.py

if %errorlevel% neq 0 goto server_error
goto end

:server_error
echo.
echo [AVISO] El servidor se ha detenido con codigo de error %errorlevel%.
pause

:end
