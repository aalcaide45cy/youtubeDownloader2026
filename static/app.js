document.addEventListener("DOMContentLoaded", () => {
    // ==========================================================================
    // SELECCIÓN DE ELEMENTOS DEL DOM
    // ==========================================================================
    const inputUrl = document.getElementById("youtube-url");
    const btnAnalyze = document.getElementById("btn-analyze");
    const btnAnalyzeText = document.getElementById("btn-analyze-text");
    const btnAnalyzeSpinner = document.getElementById("btn-analyze-spinner");
    const errorMessage = document.getElementById("error-message");
    
    const skeletonLoader = document.getElementById("skeleton-loader");
    const resultsSection = document.getElementById("results-section");
    
    // Vista previa del video
    const videoThumbnail = document.getElementById("video-thumbnail");
    const videoDuration = document.getElementById("video-duration");
    const videoTitle = document.getElementById("video-title");
    const videoChannel = document.getElementById("video-channel");
    const videoViews = document.getElementById("video-views");
    
    // Contenedores de Listas de Formatos
    const resolutionsList = document.getElementById("resolutions-list");
    const audiosList = document.getElementById("audios-list");
    const subtitlesList = document.getElementById("subtitles-list");
    
    // Botones de Pestañas (Tabs)
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");
    
    // Carpeta de Descarga y Botones de Descarga
    const downloadFolderPath = document.getElementById("download-folder-path");
    const btnChangeFolder = document.getElementById("btn-change-folder");
    const btnDownload = document.getElementById("btn-download");
    const selectedCount = document.getElementById("selected-count");
    
    // Selector de cookies del navegador
    const browserCookies = document.getElementById("browser-cookies");

    // Vistas de resultados individuales vs playlists
    const singleVideoResults = document.getElementById("single-video-results");
    const playlistResults = document.getElementById("playlist-results");
    
    // Vista previa de playlist
    const playlistThumbnail = document.getElementById("playlist-thumbnail");
    const playlistCount = document.getElementById("playlist-count");
    const playlistTitle = document.getElementById("playlist-title");
    const playlistChannel = document.getElementById("playlist-channel");
    
    // Controles de playlist
    const playlistToggleAll = document.getElementById("playlist-toggle-all");
    const playlistDownloadMode = document.getElementById("playlist-download-mode");
    const playlistVideosList = document.getElementById("playlist-videos-list");
    
    // Sección de Descargas Activas
    const downloadsSection = document.getElementById("downloads-section");
    const downloadsProgressList = document.getElementById("downloads-progress-list");
    const downloadsTotalBadge = document.getElementById("downloads-total-badge");

    // ==========================================================================
    // ESTADO DE LA APLICACIÓN
    // ==========================================================================
    let currentVideoData = null; // Almacena el resultado del análisis
    let selectedItems = new Map(); // Mapa de elementos seleccionados (key: item_id, value: item_object)
    let selectedPlaylistItems = new Map(); // Mapa de videos seleccionados de la playlist (key: entry_id, value: entry_object)
    let currentDownloadFolder = ""; // Ruta actual de descarga

    // Cargar carpeta predeterminada al iniciar
    fetch("/api/default-folder")
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                currentDownloadFolder = data.folder;
                downloadFolderPath.textContent = currentDownloadFolder;
                downloadFolderPath.title = currentDownloadFolder;
            }
        })
        .catch(err => {
            console.error("Error al obtener carpeta de descarga predeterminada:", err);
            downloadFolderPath.textContent = "Error al cargar la carpeta";
        });

    // ==========================================================================
    // SOPORTE DE PESTAÑAS (TABS)
    // ==========================================================================
    tabButtons.forEach(button => {
        button.addEventListener("click", () => {
            const targetTabId = button.getAttribute("data-tab");
            
            // Desactivar botones y paneles
            tabButtons.forEach(btn => btn.classList.remove("active"));
            tabPanes.forEach(pane => pane.classList.remove("active"));
            
            // Activar actual
            button.classList.add("active");
            document.getElementById(targetTabId).classList.add("active");
        });
    });

    // ==========================================================================
    // ANALIZAR VIDEO DE YOUTUBE
    // ==========================================================================
    btnAnalyze.addEventListener("click", analyzeVideo);
    inputUrl.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            analyzeVideo();
        }
    });

    async function analyzeVideo() {
        const url = inputUrl.value.trim();
        if (!url) {
            showError("Por favor, introduce una URL de YouTube.");
            return;
        }

        // Limpiar errores y estados previos
        hideError();
        resultsSection.classList.add("hidden");
        selectedItems.clear();
        selectedPlaylistItems.clear();
        playlistToggleAll.checked = false;
        updateDownloadButtonState();
        
        // Mostrar esqueleto de carga y spinner de botón
        setAnalyzingState(true);

        try {
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ url, browser: browserCookies.value })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Error al analizar el video.");
            }

            currentVideoData = data;
            
            if (data.is_playlist) {
                // Ocultar vista individual, mostrar vista playlist
                singleVideoResults.classList.add("hidden");
                playlistResults.classList.remove("hidden");
                renderPlaylistInfo(data.meta);
                renderPlaylist(data);
            } else {
                // Mostrar vista individual, ocultar vista playlist
                singleVideoResults.classList.remove("hidden");
                playlistResults.classList.add("hidden");
                renderVideoInfo(data.meta);
                renderFormats(data);
            }
            
            // Mostrar los resultados
            resultsSection.classList.remove("hidden");
        } catch (err) {
            showError(err.message);
        } finally {
            setAnalyzingState(false);
        }
    }

    function setAnalyzingState(isAnalyzing) {
        if (isAnalyzing) {
            btnAnalyze.disabled = true;
            btnAnalyzeText.classList.add("hidden");
            btnAnalyzeSpinner.classList.remove("hidden");
            skeletonLoader.classList.remove("hidden");
        } else {
            btnAnalyze.disabled = false;
            btnAnalyzeText.classList.remove("hidden");
            btnAnalyzeSpinner.classList.add("hidden");
            skeletonLoader.classList.add("hidden");
        }
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove("hidden");
    }

    function hideError() {
        errorMessage.textContent = "";
        errorMessage.classList.add("hidden");
    }

    // ==========================================================================
    // RENDERIZAR RESULTADOS DEL ANÁLISIS
    // ==========================================================================
    function renderVideoInfo(meta) {
        videoThumbnail.src = meta.thumbnail || "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500";
        videoDuration.textContent = meta.duration_string || "00:00";
        videoTitle.textContent = meta.title || "Sin título";
        videoChannel.innerHTML = `<i class="fas fa-user-circle"></i> ${escapeHtml(meta.channel)}`;
        
        if (meta.views_string) {
            videoViews.innerHTML = `<i class="fas fa-eye"></i> ${meta.views_string} vistas`;
            videoViews.classList.remove("hidden");
        } else {
            videoViews.classList.add("hidden");
        }
    }

    function renderFormats(data) {
        // 1. Limpiar contenedores
        resolutionsList.innerHTML = "";
        audiosList.innerHTML = "";
        subtitlesList.innerHTML = "";

        // 2. Renderizar Resoluciones (Video)
        if (data.video_formats && data.video_formats.length > 0) {
            data.video_formats.forEach(f => {
                let videoNote = f.acodec !== 'none' ? "Video + Audio integrados" : "Solo Video (Audio combinado automáticamente)";
                let infoParts = [];
                if (f.vbr_string) infoParts.push(`Tasa: ${f.vbr_string}`);
                if (f.codec_name) infoParts.push(`Códec: ${f.codec_name}`);
                if (infoParts.length > 0) {
                    videoNote += " | " + infoParts.join(" | ");
                }

                const item = createFormatRow({
                    id: `v-${f.format_id}`,
                    type: "video",
                    val: f.format_id,
                    title: f.resolution_name,
                    note: videoNote,
                    size: f.filesize_string,
                    badgeClass: "badge-video-tag",
                    badgeText: "Video"
                });
                resolutionsList.appendChild(item);
            });
        } else {
            resolutionsList.innerHTML = `<p class="option-note" style="text-align:center; padding:2rem;">No se encontraron formatos de video.</p>`;
        }

        // 3. Renderizar Audios
        if (data.audio_formats && data.audio_formats.length > 0) {
            data.audio_formats.forEach(f => {
                let audioNote = `Formato de audio puro (.${f.ext})`;
                if (f.codec_name) {
                    audioNote += ` | Códec: ${f.codec_name}`;
                }

                const item = createFormatRow({
                    id: `a-${f.format_id}`,
                    type: "audio",
                    val: f.format_id,
                    title: f.audio_name,
                    note: audioNote,
                    size: f.filesize_string,
                    badgeClass: "badge-audio-tag",
                    badgeText: "Audio"
                });
                audiosList.appendChild(item);
            });
        } else {
            audiosList.innerHTML = `<p class="option-note" style="text-align:center; padding:2rem;">No se encontraron formatos de audio.</p>`;
        }

        // 4. Renderizar Subtítulos
        if (data.subtitles && data.subtitles.length > 0) {
            data.subtitles.forEach(s => {
                const item = createFormatRow({
                    id: `s-${s.code}`,
                    type: "subtitle",
                    val: s.code,
                    title: s.name,
                    note: `Subtítulo tipo ${s.type}`,
                    size: s.type, // Usamos la sección derecha para el tipo en lugar de tamaño
                    isSubtitle: true
                });
                subtitlesList.appendChild(item);
            });
        } else {
            subtitlesList.innerHTML = `<p class="option-note" style="text-align:center; padding:2rem;">No se encontraron subtítulos para este video.</p>`;
        }
    }

    function createFormatRow(info) {
        const row = document.createElement("div");
        row.className = "option-row";
        row.id = info.id;

        const isSub = info.isSubtitle;

        row.innerHTML = `
            <div class="option-left">
                <div class="checkbox-custom-wrapper">
                    <input type="checkbox" id="chk-${info.id}">
                    <span class="checkbox-checkmark"></span>
                </div>
                <div class="option-details">
                    <span class="option-name">${escapeHtml(info.title)}</span>
                    <span class="option-note">${escapeHtml(info.note)}</span>
                </div>
            </div>
            <div class="option-right">
                ${isSub ? `<span class="badge" style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08);">${info.size}</span>` : `
                    <span class="option-size">${info.size}</span>
                    <span class="badge-tag ${info.badgeClass}">${info.badgeText}</span>
                `}
            </div>
        `;

        // Permitir seleccionar haciendo clic en toda la fila
        row.addEventListener("click", (e) => {
            // Evitar que el clic en el checkbox real dispare doble evento
            if (e.target.tagName === "INPUT") return;
            
            const chk = row.querySelector("input[type='checkbox']");
            chk.checked = !chk.checked;
            toggleRowSelection(row, chk.checked, info);
        });

        const checkbox = row.querySelector("input[type='checkbox']");
        checkbox.addEventListener("change", () => {
            toggleRowSelection(row, checkbox.checked, info);
        });

        return row;
    }

    function toggleRowSelection(row, isChecked, info) {
        if (isChecked) {
            row.classList.add("selected");
            selectedItems.set(info.id, info);
        } else {
            row.classList.remove("selected");
            selectedItems.delete(info.id);
        }
        updateDownloadButtonState();
    }

    function updateDownloadButtonState() {
        const isPlaylist = currentVideoData && currentVideoData.is_playlist;
        const count = isPlaylist ? selectedPlaylistItems.size : selectedItems.size;
        selectedCount.textContent = count;
        btnDownload.disabled = count === 0;
    }

    // ==========================================================================
    // RENDERIZAR RESULTADOS DE LISTA DE REPRODUCCIÓN (PLAYLIST)
    // ==========================================================================
    function renderPlaylistInfo(meta) {
        playlistThumbnail.src = meta.thumbnail || "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500";
        playlistCount.textContent = `${meta.video_count} videos`;
        playlistTitle.textContent = meta.title || "Lista de reproducción sin título";
        playlistChannel.innerHTML = `<i class="fas fa-list-ul"></i> ${escapeHtml(meta.channel)}`;
    }

    function renderPlaylist(data) {
        playlistVideosList.innerHTML = "";
        
        if (data.entries && data.entries.length > 0) {
            data.entries.forEach((entry, idx) => {
                const item = createPlaylistRow(entry, idx);
                playlistVideosList.appendChild(item);
            });
        } else {
            playlistVideosList.innerHTML = `<p class="option-note" style="text-align:center; padding:2rem;">No se encontraron videos en la lista.</p>`;
        }
    }

    function createPlaylistRow(entry, index) {
        const row = document.createElement("div");
        row.className = "option-row";
        row.id = `pl-item-${entry.id}`;

        row.innerHTML = `
            <div class="option-left" style="flex: 1; overflow: hidden;">
                <div class="checkbox-custom-wrapper">
                    <input type="checkbox" id="chk-pl-${entry.id}">
                    <span class="checkbox-checkmark"></span>
                </div>
                <img src="${entry.thumbnail || 'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=50'}" alt="" style="width: 50px; height: 28px; object-fit: cover; border-radius: 4px; margin-left: 0.5rem; border: 1px solid rgba(255,255,255,0.05); flex-shrink: 0;">
                <div class="option-details" style="margin-left: 0.5rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    <span class="option-name" style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block;">${index + 1}. ${escapeHtml(entry.title)}</span>
                    <span class="option-note">${escapeHtml(entry.channel || 'Canal desconocido')}</span>
                </div>
            </div>
            <div class="option-right" style="flex-shrink: 0;">
                <span class="option-size">${entry.duration_string || '00:00'}</span>
            </div>
        `;

        row.addEventListener("click", (e) => {
            if (e.target.tagName === "INPUT") return;
            const chk = row.querySelector("input[type='checkbox']");
            chk.checked = !chk.checked;
            togglePlaylistRowSelection(row, chk.checked, entry);
        });

        const checkbox = row.querySelector("input[type='checkbox']");
        checkbox.addEventListener("change", () => {
            togglePlaylistRowSelection(row, checkbox.checked, entry);
        });

        return row;
    }

    function togglePlaylistRowSelection(row, isChecked, entry) {
        if (isChecked) {
            row.classList.add("selected");
            selectedPlaylistItems.set(entry.id, entry);
        } else {
            row.classList.remove("selected");
            selectedPlaylistItems.delete(entry.id);
            playlistToggleAll.checked = false;
        }
        updateDownloadButtonState();
    }

    playlistToggleAll.addEventListener("change", () => {
        const isChecked = playlistToggleAll.checked;
        const checkboxes = playlistVideosList.querySelectorAll("input[type='checkbox']");
        
        checkboxes.forEach(chk => {
            if (chk.checked !== isChecked) {
                chk.checked = isChecked;
                const event = new Event('change');
                chk.dispatchEvent(event);
            }
        });
    });

    function escapeHtml(text) {
        if (!text) return "";
        return text
            .toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // ==========================================================================
    // CAMBIAR CARPETA DE DESCARGA (TKINTER NATIVO)
    // ==========================================================================
    btnChangeFolder.addEventListener("click", async () => {
        btnChangeFolder.disabled = true;
        const btnText = btnChangeFolder.querySelector("span");
        const originalText = btnText.textContent;
        btnText.textContent = "Eligiendo...";

        try {
            const res = await fetch("/api/select-folder", { method: "POST" });
            const data = await res.json();

            if (data.status === "success" && data.folder) {
                currentDownloadFolder = data.folder;
                downloadFolderPath.textContent = currentDownloadFolder;
                downloadFolderPath.title = currentDownloadFolder;
            } else if (data.status === "error") {
                alert("Error al abrir selector de carpetas: " + data.message);
            }
        } catch (err) {
            console.error("Error en select-folder:", err);
            alert("No se pudo conectar con el servidor para elegir la carpeta.");
        } finally {
            btnChangeFolder.disabled = false;
            btnText.textContent = originalText;
        }
    });

    // ==========================================================================
    // DESCARGAR ELEMENTOS CON SSE EN TIEMPO REAL
    // ==========================================================================
    btnDownload.addEventListener("click", startDownloads);

    async function startDownloads() {
        const isPlaylist = currentVideoData && currentVideoData.is_playlist;
        const count = isPlaylist ? selectedPlaylistItems.size : selectedItems.size;
        if (count === 0) return;

        // Desactivar interfaz durante descargas activas para evitar conflictos
        btnDownload.disabled = true;
        inputUrl.disabled = true;
        btnAnalyze.disabled = true;

        // Limpiar y mostrar el panel de descargas activas
        downloadsProgressList.innerHTML = "";
        downloadsSection.classList.remove("hidden");
        downloadsTotalBadge.textContent = `${count} descarga(s)`;

        let itemsPayload = [];
        
        if (isPlaylist) {
            const mode = playlistDownloadMode.value; // e.g., 'video_1080' or 'audio_320'
            const itemType = mode.startsWith('video_') ? 'video' : 'audio';
            itemsPayload = Array.from(selectedPlaylistItems.values()).map(entry => ({
                id: `pl-${entry.id}`,
                url: entry.url,
                type: itemType,
                val: mode,
                title: entry.title
            }));
            
            selectedPlaylistItems.forEach((entry) => {
                createProgressCard({
                    id: `pl-${entry.id}`,
                    type: itemType,
                    title: entry.title
                });
            });
        } else {
            // Detectar si hay un audio seleccionado de forma cruzada para combinar con los vídeos
            const selectedAudio = Array.from(selectedItems.values()).find(info => info.type === 'audio');

            // Formatear items para enviar a la API
            itemsPayload = Array.from(selectedItems.values()).map(info => {
                const item = {
                    id: info.id,
                    url: inputUrl.value.trim(),
                    type: info.type,
                    val: info.val,
                    title: `${currentVideoData.meta.title} (${info.title})`
                };
                // Si es video y el usuario seleccionó un audio de idioma específico, lo asociamos para fusión
                if (info.type === "video" && selectedAudio) {
                    item.audio_val = selectedAudio.val;
                }
                return item;
            });

            // Crear elementos de progreso en la UI para cada item antes de iniciar
            selectedItems.forEach((info) => {
                createProgressCard(info);
            });
        }

        try {
            const response = await fetch("/api/download", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    items: itemsPayload,
                    download_dir: currentDownloadFolder,
                    browser: browserCookies.value
                })
            });

            if (!response.ok) {
                throw new Error("No se pudo iniciar el flujo de descarga.");
            }

            // Procesar el flujo SSE
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                // Guardar la última línea incompleta en el buffer
                buffer = lines.pop();

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (trimmed.startsWith("data: ")) {
                        const jsonStr = trimmed.slice(6);
                        try {
                            const eventData = JSON.parse(jsonStr);
                            handleSSEEvent(eventData);
                        } catch (e) {
                            console.error("Error al decodificar evento SSE:", e, trimmed);
                        }
                    }
                }
            }
        } catch (err) {
            console.error("Error de descarga:", err);
            // Marcar todos los elementos pendientes con error
            const sourceItems = isPlaylist ? selectedPlaylistItems : selectedItems;
            sourceItems.forEach((info) => {
                const itemId = isPlaylist ? `pl-${info.id}` : info.id;
                const card = document.getElementById(`progress-card-${itemId}`);
                if (card) {
                    updateCardStatus(card, {
                        id: itemId,
                        status: "failed",
                        error: err.message || "Error de red o conexión perdida."
                    });
                }
            });
        } finally {
            // Reactivar interfaz
            inputUrl.disabled = false;
            btnAnalyze.disabled = false;
            updateDownloadButtonState();
        }
    }

    // ==========================================================================
    // GESTIÓN DE TARJETAS DE PROGRESO DE DESCARGA
    // ==========================================================================
    function createProgressCard(info) {
        const card = document.createElement("div");
        card.className = "progress-card";
        card.id = `progress-card-${info.id}`;

        const icon = info.type === 'video' ? 'tv' : (info.type === 'audio' ? 'volume-up' : 'closed-captioning');
        
        card.innerHTML = `
            <div class="progress-info">
                <span class="progress-name">
                    <i class="fas fa-${icon}"></i> ${escapeHtml(info.title)}
                </span>
                <span class="progress-meta" id="progress-meta-${info.id}">Preparando...</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" id="progress-bar-fill-${info.id}"></div>
            </div>
            <div class="progress-footer">
                <span class="progress-status status-waiting" id="progress-status-${info.id}">
                    <i class="fas fa-clock fa-spin"></i> En cola
                </span>
                <span id="progress-speed-eta-${info.id}">-</span>
            </div>
        `;

        downloadsProgressList.appendChild(card);
    }

    function handleSSEEvent(event) {
        if (event.status === "done") {
            console.log("Descargas completadas!");
            return;
        }

        const card = document.getElementById(`progress-card-${event.id}`);
        if (!card) return;

        updateCardStatus(card, event);
    }

    function updateCardStatus(card, event) {
        const itemId = event.id;
        const fillBar = card.querySelector(`#progress-bar-fill-${itemId}`);
        const metaText = card.querySelector(`#progress-meta-${itemId}`);
        const statusSpan = card.querySelector(`#progress-status-${itemId}`);
        const speedEtaSpan = card.querySelector(`#progress-speed-eta-${itemId}`);

        if (event.status === "started") {
            statusSpan.className = "progress-status status-downloading";
            statusSpan.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Iniciando...`;
            metaText.textContent = "Conectando...";
        } 
        else if (event.status === "progress") {
            const data = event.data;
            if (data.status === "downloading") {
                const percent = data.percentage || 0;
                fillBar.style.width = `${percent}%`;
                metaText.textContent = `${percent}%`;
                
                statusSpan.className = "progress-status status-downloading";
                statusSpan.innerHTML = `<i class="fas fa-arrow-down-long animate-bounce-slow"></i> Descargando`;
                speedEtaSpan.textContent = `${data.speed} | ETA: ${data.eta}`;
            }
        } 
        else if (event.status === "completed") {
            fillBar.style.width = "100%";
            metaText.textContent = "100%";
            
            statusSpan.className = "progress-status status-finished";
            statusSpan.innerHTML = `<i class="fas fa-circle-check"></i> Completado`;
            
            // Reemplazar el texto de velocidad con un botón interactivo de abrir carpeta
            speedEtaSpan.innerHTML = `
                <button class="btn-open-folder" title="Abrir carpeta de descargas en Windows Explorer">
                    <i class="fas fa-folder-open"></i> Abrir Carpeta
                </button>
            `;
            
            const btnOpen = speedEtaSpan.querySelector(".btn-open-folder");
            btnOpen.addEventListener("click", () => {
                fetch("/api/open-folder", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ folder_path: currentDownloadFolder })
                }).catch(err => console.error("Error al abrir carpeta:", err));
            });
            
            // Animación suave de éxito
            card.style.boxShadow = "0 0 10px rgba(16, 185, 129, 0.15)";
            card.style.borderColor = "var(--success)";
        } 
        else if (event.status === "failed") {
            statusSpan.className = "progress-status status-error";
            statusSpan.innerHTML = `<i class="fas fa-triangle-exclamation"></i> Error`;
            speedEtaSpan.textContent = "";
            metaText.textContent = "Fallo";
            
            card.style.borderColor = "var(--error)";
            card.style.boxShadow = "0 0 10px rgba(239, 68, 68, 0.15)";
            
            // Añadir explicación del error abajo de la tarjeta si no existía ya
            let errorDiv = card.querySelector(".error-detail");
            if (!errorDiv) {
                errorDiv = document.createElement("div");
                errorDiv.className = "error-detail";
                errorDiv.style.fontSize = "0.75rem";
                errorDiv.style.color = "var(--error)";
                errorDiv.style.marginTop = "0.5rem";
                errorDiv.style.wordBreak = "break-word";
                card.appendChild(errorDiv);
            }
            errorDiv.textContent = event.error || "Ocurrió un error inesperado al descargar.";
        }
    }
});
