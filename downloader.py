import os
import yt_dlp

COMMON_LANGUAGES = {
    'es': 'Español',
    'en': 'Inglés',
    'fr': 'Francés',
    'de': 'Alemán',
    'it': 'Italiano',
    'pt': 'Portugués',
    'ja': 'Japonés',
    'zh': 'Chino',
    'ru': 'Ruso',
    'ko': 'Coreano',
    'ar': 'Árabe',
    'hi': 'Hindi',
    'en-US': 'Inglés (EE. UU.)',
    'en-GB': 'Inglés (Reino Unido)',
    'es-ES': 'Español (España)',
    'es-419': 'Español (Latinoamérica)',
}

def get_language_name(code):
    if not code:
        return None
    # Limpiar posibles sufijos (ej: es-ES -> es, en-US -> en) o buscar coincidencia exacta primero
    name = COMMON_LANGUAGES.get(code)
    if not name and '-' in code:
        base_code = code.split('-')[0]
        name = COMMON_LANGUAGES.get(base_code)
    return name or code

def format_size(size_in_bytes):
    if not size_in_bytes:
        return "Desconocido"
    size = float(size_in_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def format_duration(seconds):
    if not seconds:
        return "00:00"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def extract_video_info(url, browser_name=None):
    """
    Extrae la información del video usando yt-dlp, opcionalmente cargando cookies de un navegador.
    """
    ydl_opts = {
        'skip_download': True,
        'youtube_include_dash_manifest': False,
        'quiet': True,
        'no_warnings': True,
    }
    
    if browser_name and browser_name.lower() != "none":
        ydl_opts['cookiesfrombrowser'] = (browser_name.lower(),)
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as e:
            # Capturar errores comunes de cookies bloqueadas
            msg = str(e)
            if "cookie" in msg.lower() or "browser" in msg.lower():
                raise RuntimeError(
                    f"Error de cookies del navegador '{browser_name}'. "
                    f"Por favor, cierra tu navegador por completo para desbloquear su base de datos de cookies e inténtalo de nuevo."
                )
            raise RuntimeError(f"Error al analizar el enlace de YouTube: {msg}")
        except Exception as e:
            raise RuntimeError(f"Error inesperado al analizar el video: {str(e)}")
            
        if not info:
            raise RuntimeError("No se pudo obtener información del video.")

        # Metadatos del video
        meta = {
            'id': info.get('id'),
            'title': info.get('title'),
            'duration': info.get('duration'),
            'duration_string': format_duration(info.get('duration', 0)),
            'thumbnail': info.get('thumbnail') or (info.get('thumbnails')[-1]['url'] if info.get('thumbnails') else None),
            'channel': info.get('uploader') or info.get('channel') or "Canal Desconocido",
            'views': info.get('view_count'),
            'views_string': f"{info.get('view_count', 0):,}".replace(",", ".") if info.get('view_count') is not None else None
        }

        formats = info.get('formats', [])
        
        # Filtrar formatos de video
        video_formats = []
        seen_resolutions = set()
        
        for f in formats:
            if f.get('vcodec') != 'none':
                height = f.get('height')
                if not height:
                    continue
                ext = f.get('ext')
                fps = f.get('fps')
                filesize = f.get('filesize') or f.get('filesize_approx')
                
                res_key = f"{height}p_{ext}"
                
                if res_key in seen_resolutions:
                    idx = next(i for i, vf in enumerate(video_formats) if vf['height'] == height and vf['ext'] == ext)
                    old_f = video_formats[idx]
                    old_fps = old_f['fps'] or 0
                    current_fps = fps or 0
                    if current_fps > old_fps or (not old_f['filesize'] and filesize):
                        video_formats[idx] = {
                            'format_id': f.get('format_id'),
                            'height': height,
                            'fps': fps,
                            'ext': ext,
                            'filesize': filesize,
                            'filesize_string': format_size(filesize) if filesize else "Estimado: " + format_size(f.get('filesize_approx')),
                            'resolution_name': f"{height}p ({ext.upper()})" + (f" - {fps}fps" if fps else ""),
                            'acodec': f.get('acodec')
                        }
                    continue
                    
                seen_resolutions.add(res_key)
                video_formats.append({
                    'format_id': f.get('format_id'),
                    'height': height,
                    'fps': fps,
                    'ext': ext,
                    'filesize': filesize,
                    'filesize_string': format_size(filesize) if filesize else ("Estimado: " + format_size(f.get('filesize_approx')) if f.get('filesize_approx') else "Desconocido"),
                    'resolution_name': f"{height}p ({ext.upper()})" + (f" - {fps}fps" if fps else ""),
                    'acodec': f.get('acodec')
                })

        # Ordenar videos por resolución descendente
        video_formats.sort(key=lambda x: (x['height'], x['fps'] or 0), reverse=True)

        # Filtrar formatos de audio (solo audio)
        audio_formats = []
        seen_audios = set()
        
        for f in formats:
            if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                ext = f.get('ext')
                abr = f.get('abr')
                filesize = f.get('filesize') or f.get('filesize_approx')
                
                # Extraer idioma si existe
                lang = f.get('language')
                lang_code = lang if (lang and lang != 'und') else None
                lang_name = get_language_name(lang_code)
                
                # Agregamos idioma a la clave de unicidad para listar los distintos idiomas disponibles
                audio_key = f"{ext}_{abr}_{lang_code}"
                if audio_key in seen_audios:
                    continue
                seen_audios.add(audio_key)
                
                audio_name = f"{ext.upper()} - {int(abr)} kbps" if abr else f"{ext.upper()} - Calidad estándar"
                if lang_name:
                    audio_name += f" ({lang_name})"
                
                audio_formats.append({
                    'format_id': f.get('format_id'),
                    'ext': ext,
                    'abr': abr,
                    'filesize': filesize,
                    'filesize_string': format_size(filesize) if filesize else ("Estimado: " + format_size(f.get('filesize_approx')) if f.get('filesize_approx') else "Desconocido"),
                    'audio_name': audio_name,
                    'language': lang_code,
                    'language_name': lang_name
                })
                
        # Ordenar audios por bitrate descendente
        audio_formats.sort(key=lambda x: x['abr'] or 0, reverse=True)

        # Subtítulos
        subtitles = []
        
        # Manuales
        manual_subs = info.get('subtitles', {})
        for lang_code in manual_subs.keys():
            subtitles.append({
                'code': lang_code,
                'name': get_language_name(lang_code),
                'type': 'Manual'
            })
            
        # Automáticos
        auto_subs = info.get('automatic_captions', {})
        for lang_code in auto_subs.keys():
            if not any(s['code'] == lang_code for s in subtitles):
                subtitles.append({
                    'code': lang_code,
                    'name': get_language_name(lang_code) + " (Auto)",
                    'type': 'Automático'
                })

        # Ordenar subtítulos alfabéticamente
        subtitles.sort(key=lambda x: x['name'])

        return {
            'meta': meta,
            'video_formats': video_formats,
            'audio_formats': audio_formats,
            'subtitles': subtitles
        }

class DownloadProgressHook:
    def __init__(self, callback, item_id):
        self.callback = callback
        self.item_id = item_id

    def __call__(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            percentage = (downloaded / total * 100) if total > 0 else 0
            speed = d.get('speed') # bytes/seg
            speed_str = format_size(speed) + "/s" if speed else "Calculando..."
            eta = d.get('eta') # segundos
            eta_str = f"{eta}s" if eta is not None else "Desconocido"
            
            self.callback({
                'id': self.item_id,
                'status': 'downloading',
                'downloaded': downloaded,
                'total': total,
                'percentage': round(percentage, 1),
                'speed': speed_str,
                'eta': eta_str
            })
        elif d['status'] == 'finished':
            self.callback({
                'id': self.item_id,
                'status': 'finished',
                'percentage': 100,
                'filename': os.path.basename(d.get('filename', ''))
            })

def download_item(url, item_type, selection_val, download_dir, progress_callback, item_id, browser_name=None, associated_audio_val=None):
    """
    Descarga un elemento específico en la carpeta indicada.
    """
    ydl_opts = {
        'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
        'progress_hooks': [DownloadProgressHook(progress_callback, item_id)],
        'quiet': True,
        'no_warnings': True,
    }
    
    if browser_name and browser_name.lower() != "none":
        ydl_opts['cookiesfrombrowser'] = (browser_name.lower(),)
    
    if item_type == 'video':
        # Si hay un audio específico seleccionado (ej: en español), fusionamos con ese format_id
        if associated_audio_val:
            ydl_opts['format'] = f"{selection_val}+{associated_audio_val}"
        else:
            ydl_opts['format'] = f"{selection_val}+bestaudio/best"
        ydl_opts['merge_output_format'] = 'mp4'
    elif item_type == 'audio':
        ydl_opts['format'] = selection_val
    elif item_type == 'subtitle':
        ydl_opts['skip_download'] = True
        ydl_opts['writesubtitles'] = True
        ydl_opts['subtitleslangs'] = [selection_val]
        ydl_opts['subtitlesformat'] = 'srt/vtt'
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except yt_dlp.utils.DownloadError as e:
            msg = str(e)
            if "cookie" in msg.lower() or "browser" in msg.lower():
                err_msg = (
                    f"Error de cookies. Por favor, cierra tu navegador '{browser_name}' "
                    f"completamente para liberar la base de datos de cookies e inténtalo de nuevo."
                )
            else:
                err_msg = msg
            progress_callback({
                'id': item_id,
                'status': 'error',
                'error': err_msg
            })
            raise RuntimeError(err_msg)
        except Exception as e:
            progress_callback({
                'id': item_id,
                'status': 'error',
                'error': str(e)
            })
            raise e
