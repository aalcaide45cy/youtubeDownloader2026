import os
import sys
import json
import queue
import threading
import pathlib
import webbrowser
from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor

# Importar funciones de descarga
from downloader import extract_video_info, download_item, format_size

app = FastAPI(title="YouTube Downloader Premium API")

# Habilitar CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definir la ruta de descarga predeterminada (carpeta Descargas del usuario)
DEFAULT_DOWNLOAD_DIR = str(pathlib.Path.home() / "Downloads")

class AnalyzeRequest(BaseModel):
    url: str
    browser: Optional[str] = None

class DownloadItemRequest(BaseModel):
    id: str
    type: str # 'video', 'audio', or 'subtitle'
    val: str  # format_id o idioma del subtítulo
    audio_val: Optional[str] = None # ID de audio específico asociado para combinar con el video

class DownloadRequest(BaseModel):
    url: str
    items: List[DownloadItemRequest]
    download_dir: Optional[str] = None
    browser: Optional[str] = None

@app.get("/api/default-folder")
def get_default_folder():
    """
    Retorna la carpeta de descargas predeterminada del usuario.
    """
    return {
        "status": "success",
        "folder": os.path.normpath(DEFAULT_DOWNLOAD_DIR)
    }

@app.post("/api/analyze")
def analyze_video(request: AnalyzeRequest):
    """
    Analiza un enlace de YouTube y retorna los formatos de video, audio y subtítulos disponibles.
    """
    if not request.url:
        raise HTTPException(status_code=400, detail="Se requiere una URL válida.")
    try:
        info = extract_video_info(request.url, request.browser)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/select-folder")
def select_folder():
    """
    Abre el diálogo nativo de Windows (tkinter) para elegir una carpeta de descarga.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Necesitamos inicializar Tk de forma segura en este hilo
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True) # Forzar ventana al frente
        
        # Mostrar el diálogo de selección de carpeta
        folder = filedialog.askdirectory(
            title="Seleccionar Carpeta para Guardar Descargas",
            initialdir=DEFAULT_DOWNLOAD_DIR
        )
        root.destroy()
        
        if folder:
            return {"status": "success", "folder": os.path.normpath(folder)}
        else:
            return {"status": "cancelled", "folder": None}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/download")
def download_stream(request: DownloadRequest):
    """
    Inicia la descarga de los elementos seleccionados de forma concurrente
    y transmite el progreso en tiempo real usando Server-Sent Events (SSE).
    """
    download_dir = request.download_dir or DEFAULT_DOWNLOAD_DIR
    if not os.path.exists(download_dir):
        try:
            os.makedirs(download_dir, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No se pudo crear el directorio de descarga: {str(e)}")

    q = queue.Queue()

    def run_downloads():
        # Descarga concurrente: máximo 4 descargas en paralelo
        max_workers = min(len(request.items), 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for item in request.items:
                item_id = item.id
                item_type = item.type
                val = item.val
                audio_val = item.audio_val
                
                # Función que envolverá la llamada individual de descarga
                def download_task(i_id, i_type, v, a_v):
                    try:
                        # Notificar inicio de la descarga
                        q.put({
                            "id": i_id,
                            "status": "started",
                            "type": i_type
                        })
                        
                        def progress_callback(data):
                            q.put({
                                "id": i_id,
                                "status": "progress",
                                "data": data
                            })
                        
                        download_item(
                            request.url,
                            i_type,
                            v,
                            download_dir,
                            progress_callback,
                            i_id,
                            browser_name=request.browser,
                            associated_audio_val=a_v
                        )
                        
                        # Notificar completado
                        q.put({
                            "id": i_id,
                            "status": "completed"
                        })
                    except Exception as e:
                        # Notificar error
                        q.put({
                            "id": i_id,
                            "status": "failed",
                            "error": str(e)
                        })

                # Lanzar tarea en el pool de hilos
                futures.append(executor.submit(download_task, item_id, item_type, val, audio_val))
            
            # Esperar a que terminen todas las descargas del pool
            for future in futures:
                future.result()

        # Notificar fin de todo el lote de descargas
        q.put({"status": "done"})

    # Iniciar la descarga en un hilo secundario para no bloquear el bucle de FastAPI
    threading.Thread(target=run_downloads, daemon=True).start()

    # Generador de eventos SSE
    def event_generator():
        while True:
            try:
                msg = q.get(timeout=180) # Espera máxima de 3 minutos por evento
                if msg.get("status") == "done":
                    yield f"data: {json.dumps({'status': 'done'})}\n\n"
                    break
                yield f"data: {json.dumps(msg)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'status': 'error', 'error': 'Tiempo de espera agotado en la descarga'})}\n\n"
                break
            except Exception as e:
                yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Montar los archivos estáticos del frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

def open_browser():
    """Abre el navegador en el host local tras una breve pausa para dejar que el servidor levante."""
    import time
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    import uvicorn
    # Lanzar hilo para abrir navegador
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Iniciar el servidor
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
