# YT Downloader Premium - Servidor Local Multi-Descarga

Una aplicación web de escritorio local, de diseño premium y moderna, construida con **FastAPI** en el backend y una interfaz de usuario fluida con **Glassmorphism** en el frontend. Utiliza **yt-dlp** para analizar y descargar flujos de YouTube a la velocidad máxima de tu red.

---

## 🚀 Características Clave

1. **Multi-Descarga Concurrente (Hilos)**: 
   Descarga múltiples pistas de vídeo, audio y subtítulos en paralelo (hasta 4 descargas simultáneas) utilizando un pool de hilos (`ThreadPoolExecutor`).
2. **Selección de Idiomas de Audio**:
   Permite listar todos los idiomas de audio disponibles de un vídeo. Si seleccionas una resolución de vídeo y una pista de audio en un idioma específico (ej: Español), la aplicación descargará ambos y los fusionará automáticamente en un solo archivo `.mp4` usando FFmpeg.
3. **Login seguro por Navegador (Cookies)**:
   Evita bloqueos de edad, CAPTCHAs y accede a tus vídeos privados o de miembros cargando las cookies de sesión activa de tu navegador web preferido (Chrome, Edge, Firefox, Brave, Opera, Vivaldi, Safari) de forma segura.
4. **Selector de Carpeta Nativo**:
   Integra una ventana emergente nativa del explorador de Windows para cambiar fácilmente la carpeta donde se guardarán las descargas.
5. **Progreso en Tiempo Real**:
   Transmite de manera asíncrona la velocidad de descarga en MB/s, porcentaje y tiempo estimado (ETA) mediante Server-Sent Events (SSE).
6. **Diseño Visual de Vanguardia**:
   Interfaz de usuario responsiva estilo "Glassmorphic" con orbes brillantes de fondo, modo oscuro, skeleton loaders y transiciones fluidas.

---

## 🛠️ Requisitos de Instalación

Antes de iniciar la aplicación, asegúrate de tener instalado en tu sistema:

1. **Python 3.13** o superior.
2. **FFmpeg** añadido al PATH de tu sistema (requerido por `yt-dlp` para fusionar el audio y el vídeo de alta calidad).

---

## 💻 Cómo Iniciar (Windows)

Para facilitarte la vida, hemos incluido un script automatizado. Simplemente haz doble clic en el archivo:

👉 **`run.bat`**

Este archivo por lotes se encargará automáticamente de:
1. Comprobar si existe el entorno virtual local de Python (`.venv`). Si no, lo creará.
2. Verificar e instalar las dependencias necesarias (`fastapi`, `uvicorn`, `yt-dlp`).
3. Iniciar el servidor local de FastAPI.
4. Abrir automáticamente tu navegador de internet preferido en la dirección: **`http://127.0.0.1:8000`**.

*Para cerrar el servidor en cualquier momento, basta con cerrar la ventana de comandos negra.*

---

## 📂 Estructura del Código

- `downloader.py`: Módulo que integra `yt-dlp` para analizar vídeos de YouTube (extrayendo resoluciones, audios clasificados por idiomas y subtítulos) y realiza las descargas de forma asíncrona con hooks de progreso.
- `main.py`: Servidor FastAPI que expone la API y sirve la interfaz estática. Gestiona la concurrencia de descargas usando multi-hilo y levanta el selector de carpetas de Windows.
- `run.bat`: Script de Windows para inicialización automática.
- `static/`:
  - `index.html`: Estructura HTML de la aplicación basada en pestañas y tarjetas interactivas.
  - `style.css`: Estética visual Premium (Glassmorphism, gradientes de fondo y animaciones).
  - `app.js`: Controlador dinámico de interfaz de usuario y procesamiento de eventos SSE de descarga.
- `README.md`: Este archivo explicativo de GitHub.
