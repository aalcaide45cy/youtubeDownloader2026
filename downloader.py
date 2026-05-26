import os
import yt_dlp
import html
import re
from yt_dlp.postprocessor.common import PostProcessor

class EmojiCleanerPP(PostProcessor):
    def run(self, info):
        title = info.get('title')
        if title:
            try:
                emoji_pattern = re.compile(
                    '['
                    '\U00010000-\U0010FFFF'  # Emojis modernos y planos suplementarios
                    '\u2600-\u27BF'          # Símbolos misceláneos, dingbats, etc.
                    '\u2300-\u23FF'          # Símbolos técnicos misceláneos
                    ']+', 
                    flags=re.UNICODE
                )
                cleaned = emoji_pattern.sub('', title)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                info['title'] = cleaned
            except Exception:
                pass
        return [], info

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
    Extrae la información del enlace de YouTube (soporta vídeos individuales y playlists),
    opcionalmente cargando cookies de un navegador.
    """
    # 1. Intentar extracción rápida (plana) para verificar si es una playlist
    ydl_opts_flat = {
        'extract_flat': 'in_playlist',
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'lang': ['es']
            }
        }
    }
    
    if browser_name and browser_name.lower() != "none":
        ydl_opts_flat['cookiesfrombrowser'] = (browser_name.lower(),)
        
    with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as e:
            msg = str(e)
            if "cookie" in msg.lower() or "browser" in msg.lower():
                raise RuntimeError(
                    f"Error de cookies del navegador '{browser_name}'. "
                    f"Por favor, cierra tu navegador por completo para desbloquear su base de datos de cookies e inténtalo de nuevo."
                )
            raise RuntimeError(f"Error al analizar el enlace de YouTube: {msg}")
        except Exception as e:
            raise RuntimeError(f"Error inesperado al analizar el enlace: {str(e)}")
            
        if not info:
            raise RuntimeError("No se pudo obtener información del enlace.")

        # 2. Si es una lista de reproducción (playlist)
        if info.get('_type') == 'playlist' or 'entries' in info:
            entries_raw = info.get('entries', [])
            
            # Formatear metadatos de la playlist
            thumbnail_url = None
            if info.get('thumbnails'):
                thumbnail_url = info.get('thumbnails')[-1]['url']
            elif len(entries_raw) > 0 and entries_raw[0] and entries_raw[0].get('thumbnail'):
                thumbnail_url = entries_raw[0].get('thumbnail')

            meta = {
                'title': html.unescape(info.get('title') or "Lista de reproducción sin título"),
                'channel': html.unescape(info.get('uploader') or info.get('channel') or "Canal Desconocido"),
                'video_count': len(entries_raw),
                'thumbnail': thumbnail_url
            }

            entries = []
            for entry in entries_raw:
                if not entry:
                    continue
                entry_id = entry.get('id')
                entries.append({
                    'id': entry_id,
                    'title': html.unescape(entry.get('title') or "Vídeo sin título"),
                    'url': entry.get('url') or f"https://www.youtube.com/watch?v={entry_id}",
                    'duration': entry.get('duration'),
                    'duration_string': format_duration(entry.get('duration', 0)),
                    'thumbnail': entry.get('thumbnails')[0]['url'] if entry.get('thumbnails') else (entry.get('thumbnail') or None),
                    'channel': html.unescape(entry.get('uploader') or entry.get('channel') or "")
                })

            return {
                'is_playlist': True,
                'meta': meta,
                'entries': entries
            }

    # 3. Si es un vídeo individual, hacemos la extracción completa de formatos
    ydl_opts_full = {
        'skip_download': True,
        'youtube_include_dash_manifest': False,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'lang': ['es']
            }
        }
    }
    
    if browser_name and browser_name.lower() != "none":
        ydl_opts_full['cookiesfrombrowser'] = (browser_name.lower(),)
        
    with yt_dlp.YoutubeDL(ydl_opts_full) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            raise RuntimeError(f"Error al extraer formatos detallados del vídeo: {str(e)}")
            
        if not info:
            raise RuntimeError("No se pudo obtener información detallada del vídeo.")

        # Metadatos del video
        meta = {
            'id': info.get('id'),
            'title': html.unescape(info.get('title') or ""),
            'duration': info.get('duration'),
            'duration_string': format_duration(info.get('duration', 0)),
            'thumbnail': info.get('thumbnail') or (info.get('thumbnails')[-1]['url'] if info.get('thumbnails') else None),
            'channel': html.unescape(info.get('uploader') or info.get('channel') or "Canal Desconocido"),
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
                
                # Extraer bitrate de video
                vbr = f.get('vbr') or f.get('tbr')
                vbr_string = None
                if vbr:
                    if vbr >= 1000:
                        vbr_string = f"{vbr/1000:.1f} Mbps"
                    else:
                        vbr_string = f"{int(vbr)} kbps"
                
                # Limpiar nombre de códec de video
                vcodec = f.get('vcodec', '')
                if 'av01' in vcodec: codec_name = 'AV1'
                elif 'vp09' in vcodec or 'vp9' in vcodec: codec_name = 'VP9'
                elif 'avc' in vcodec or 'h264' in vcodec: codec_name = 'H.264'
                elif 'hev' in vcodec or 'h265' in vcodec: codec_name = 'H.265'
                else: codec_name = vcodec.split('.')[0].upper() if vcodec else "Desconocido"
                
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
                            'acodec': f.get('acodec'),
                            'vbr_string': vbr_string,
                            'codec_name': codec_name
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
                    'acodec': f.get('acodec'),
                    'vbr_string': vbr_string,
                    'codec_name': codec_name
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
                
                # Extraer códec de audio
                acodec = f.get('acodec', '')
                if 'mp4a' in acodec or 'aac' in acodec: codec_name = 'AAC'
                elif 'opus' in acodec: codec_name = 'Opus'
                elif 'mp3' in acodec: codec_name = 'MP3'
                else: codec_name = acodec.split('.')[0].upper() if acodec else "Desconocido"
                
                lang = f.get('language')
                lang_code = lang if (lang and lang != 'und') else None
                lang_name = get_language_name(lang_code)
                
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
                    'language_name': lang_name,
                    'codec_name': codec_name
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
            'is_playlist': False,
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
            speed = d.get('speed')
            speed_str = format_size(speed) + "/s" if speed else "Calculando..."
            eta = d.get('eta')
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
        'extractor_args': {
            'youtube': {
                'lang': ['es']
            }
        }
    }
    
    if browser_name and browser_name.lower() != "none":
        ydl_opts['cookiesfrombrowser'] = (browser_name.lower(),)
    
    if item_type == 'video':
        if selection_val.startswith('video_'):
            # Modo de resolución máxima para playlist (video_best, video_1080, video_720...)
            res = selection_val.split('_')[1]
            if res == 'best':
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            else:
                ydl_opts['format'] = f"bestvideo[height<={res}]+bestaudio/best"
        else:
            # Modo vídeo único con format_id específico
            if associated_audio_val:
                ydl_opts['format'] = f"{selection_val}+{associated_audio_val}"
            else:
                ydl_opts['format'] = f"{selection_val}+bestaudio/best"
        ydl_opts['merge_output_format'] = 'mp4'
        
    elif item_type == 'audio':
        if selection_val.startswith('audio_'):
            # Modo audio de playlist con bitrate específico (audio_320, audio_192, audio_128...)
            bitrate = selection_val.split('_')[1]
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': bitrate,
            }]
        else:
            # Modo audio único con format_id específico
            ydl_opts['format'] = selection_val
            if selection_val == 'bestaudio/best':
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
                
    elif item_type == 'subtitle':
        ydl_opts['skip_download'] = True
        ydl_opts['writesubtitles'] = True
        ydl_opts['subtitleslangs'] = [selection_val]
        ydl_opts['subtitlesformat'] = 'srt/vtt'
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.add_post_processor(EmojiCleanerPP(), when='pre_process')
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
