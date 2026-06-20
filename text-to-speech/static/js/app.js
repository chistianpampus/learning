/**
 * Text-to-Speech Toolkit – Frontend Logic
 */

document.addEventListener("DOMContentLoaded", () => {
    // --- DOM Elements ---
    const tabs = document.querySelectorAll(".tab");
    const panelTTS = document.getElementById("panel-tts");
    const panelMixer = document.getElementById("panel-mixer");

    const btnInputText = document.getElementById("btn-input-text");
    const btnInputFile = document.getElementById("btn-input-file");
    const inputTextArea = document.getElementById("input-text-area");
    const inputFileArea = document.getElementById("input-file-area");

    const textInput = document.getElementById("text-input");
    const charCount = document.getElementById("char-count");
    const charWarning = document.getElementById("char-warning");

    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const fileList = document.getElementById("file-list");

    const voiceSelect = document.getElementById("voice-select");
    const preprocessToggle = document.getElementById("preprocess-toggle");
    const preprocessPreview = document.getElementById("preprocess-preview");
    const previewStats = document.getElementById("preview-stats");
    const previewText = document.getElementById("preview-text");

    const btnGenerate = document.getElementById("btn-generate");
    const progressSection = document.getElementById("progress-section");
    const progressFill = document.getElementById("progress-fill");
    const progressText = document.getElementById("progress-text");
    const resultSection = document.getElementById("result-section");
    const resultInfo = document.getElementById("result-info");
    const audioPlayer = document.getElementById("audio-player");
    const btnDownload = document.getElementById("btn-download");

    // Mixer
    const speechInput = document.getElementById("speech-input");
    const musicInput = document.getElementById("music-input");
    const speechFilename = document.getElementById("speech-filename");
    const musicFilename = document.getElementById("music-filename");
    const musicVolume = document.getElementById("music-volume");
    const volumeValue = document.getElementById("volume-value");
    const btnMix = document.getElementById("btn-mix");
    const mixerProgressSection = document.getElementById("mixer-progress-section");
    const mixerProgressText = document.getElementById("mixer-progress-text");
    const mixerResultSection = document.getElementById("mixer-result-section");
    const mixerResultInfo = document.getElementById("mixer-result-info");
    const mixerAudioPlayer = document.getElementById("mixer-audio-player");
    const btnMixerDownload = document.getElementById("btn-mixer-download");

    const errorToast = document.getElementById("error-toast");
    const toastMessage = document.getElementById("toast-message");

    // --- State ---
    let selectedFiles = [];
    let currentFilename = "";
    let mixerFilename = "";
    let inputMode = "text"; // "text" or "file"
    let preprocessDebounce = null;

    // --- Init ---
    loadVoices();

    // --- Tab Navigation ---
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            const target = tab.dataset.tab;
            panelTTS.classList.toggle("hidden", target !== "tts");
            panelMixer.classList.toggle("hidden", target !== "mixer");
        });
    });

    // --- Input Mode Toggle ---
    btnInputText.addEventListener("click", () => {
        inputMode = "text";
        btnInputText.classList.add("active");
        btnInputFile.classList.remove("active");
        inputTextArea.classList.remove("hidden");
        inputFileArea.classList.add("hidden");
        updateGenerateButton();
    });

    btnInputFile.addEventListener("click", () => {
        inputMode = "file";
        btnInputFile.classList.add("active");
        btnInputText.classList.remove("active");
        inputFileArea.classList.remove("hidden");
        inputTextArea.classList.add("hidden");
        updateGenerateButton();
    });

    // --- Text Input ---
    textInput.addEventListener("input", () => {
        const len = textInput.value.length;
        charCount.textContent = len.toLocaleString("de-DE");
        charWarning.style.display = len > 9500 ? "inline" : "none";
        updateGenerateButton();
        updatePreprocessPreview();
    });

    // --- File Upload ---
    fileInput.addEventListener("change", (e) => {
        addFiles(e.target.files);
    });

    // Drag & Drop
    ["dragenter", "dragover"].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.add("drag-over");
        });
    });

    ["dragleave", "drop"].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.remove("drag-over");
        });
    });

    dropZone.addEventListener("drop", (e) => {
        addFiles(e.dataTransfer.files);
    });

    function addFiles(newFiles) {
        for (const file of newFiles) {
            const ext = "." + file.name.split(".").pop().toLowerCase();
            if ([".txt", ".md", ".pdf"].includes(ext)) {
                selectedFiles.push(file);
            }
        }
        renderFileList();
        updateGenerateButton();
    }

    function renderFileList() {
        fileList.innerHTML = "";
        selectedFiles.forEach((file, idx) => {
            const item = document.createElement("div");
            item.className = "file-item";
            const sizeMB = (file.size / 1024 / 1024).toFixed(1);
            item.innerHTML = `
                <span class="file-item-name">${file.name}</span>
                <span class="file-item-size">${sizeMB} MB</span>
                <button class="file-item-remove" data-idx="${idx}">✕</button>
            `;
            fileList.appendChild(item);
        });

        fileList.querySelectorAll(".file-item-remove").forEach(btn => {
            btn.addEventListener("click", () => {
                selectedFiles.splice(parseInt(btn.dataset.idx), 1);
                renderFileList();
                updateGenerateButton();
            });
        });
    }

    // --- Voice Loading ---
    async function loadVoices() {
        try {
            const res = await fetch("/api/voices");
            const data = await res.json();

            if (data.error) throw new Error(data.error);

            voiceSelect.innerHTML = "";
            data.voices.forEach(voice => {
                const option = document.createElement("option");
                option.value = voice.voice_id;
                option.textContent = voice.name;
                if (voice.voice_id === data.default_voice_id) {
                    option.selected = true;
                    option.textContent += " ⭐";
                }
                voiceSelect.appendChild(option);
            });
        } catch (err) {
            voiceSelect.innerHTML = '<option value="">Fehler beim Laden</option>';
            console.error("Voice loading error:", err);
        }
    }

    // --- Preprocess Toggle ---
    preprocessToggle.addEventListener("change", () => {
        if (preprocessToggle.checked && textInput.value.trim()) {
            preprocessPreview.classList.remove("hidden");
            updatePreprocessPreview();
        } else {
            preprocessPreview.classList.add("hidden");
        }
    });

    function updatePreprocessPreview() {
        if (!preprocessToggle.checked || !textInput.value.trim()) {
            preprocessPreview.classList.add("hidden");
            return;
        }

        clearTimeout(preprocessDebounce);
        preprocessDebounce = setTimeout(async () => {
            try {
                const res = await fetch("/api/preprocess", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        text: textInput.value,
                        source_format: "auto",
                    }),
                });
                const data = await res.json();

                if (data.error) throw new Error(data.error);

                preprocessPreview.classList.remove("hidden");
                previewStats.textContent =
                    `Original: ${data.original_length.toLocaleString("de-DE")} Zeichen → ` +
                    `Bereinigt: ${data.processed_length.toLocaleString("de-DE")} Zeichen ` +
                    `(${Math.round((1 - data.processed_length / data.original_length) * 100)}% reduziert)`;
                previewText.textContent = data.processed_text.substring(0, 2000) +
                    (data.processed_text.length > 2000 ? "\n\n[…]" : "");
            } catch (err) {
                console.error("Preprocess preview error:", err);
            }
        }, 500);
    }

    // --- Generate Button State ---
    function updateGenerateButton() {
        const hasText = inputMode === "text" && textInput.value.trim().length > 0;
        const hasFiles = inputMode === "file" && selectedFiles.length > 0;
        btnGenerate.disabled = !(hasText || hasFiles);
    }

    // --- Generate MP3 ---
    btnGenerate.addEventListener("click", async () => {
        resultSection.classList.add("hidden");
        progressSection.classList.remove("hidden");
        progressFill.style.width = "0%";
        progressText.textContent = "Generiere Audio...";
        btnGenerate.disabled = true;

        try {
            let result;

            if (inputMode === "text") {
                // Simulate progress
                progressFill.style.width = "30%";
                progressFill.classList.add("indeterminate");

                const res = await fetch("/api/convert", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        text: textInput.value,
                        voice_id: voiceSelect.value,
                        preprocess: preprocessToggle.checked,
                    }),
                });
                result = await res.json();
            } else {
                // File upload
                progressFill.classList.add("indeterminate");
                progressText.textContent = "Lade Dateien hoch...";

                const formData = new FormData();
                selectedFiles.forEach(file => formData.append("files", file));
                formData.append("voice_id", voiceSelect.value);
                formData.append("preprocess", preprocessToggle.checked);

                const res = await fetch("/api/upload", {
                    method: "POST",
                    body: formData,
                });
                result = await res.json();
            }

            progressFill.classList.remove("indeterminate");

            if (result.error) throw new Error(result.error);

            // Success
            progressFill.style.width = "100%";
            progressText.textContent = "Fertig!";

            currentFilename = result.filename;
            const sizeMB = (result.size_bytes / 1024 / 1024).toFixed(1);
            resultInfo.textContent = `${result.filename} (${sizeMB} MB)`;
            audioPlayer.src = `/api/download/${result.filename}`;

            setTimeout(() => {
                progressSection.classList.add("hidden");
                resultSection.classList.remove("hidden");
            }, 600);
        } catch (err) {
            progressSection.classList.add("hidden");
            showError(err.message);
        } finally {
            updateGenerateButton();
        }
    });

    // --- Download ---
    btnDownload.addEventListener("click", () => {
        if (currentFilename) {
            window.location.href = `/api/download/${currentFilename}`;
        }
    });

    // --- Mixer ---
    speechInput.addEventListener("change", () => {
        if (speechInput.files.length > 0) {
            speechFilename.textContent = speechInput.files[0].name;
            updateMixButton();
        }
    });

    musicInput.addEventListener("change", () => {
        if (musicInput.files.length > 0) {
            musicFilename.textContent = musicInput.files[0].name;
            updateMixButton();
        }
    });

    musicVolume.addEventListener("input", () => {
        volumeValue.textContent = musicVolume.value;
    });

    function updateMixButton() {
        btnMix.disabled = !(speechInput.files.length > 0 && musicInput.files.length > 0);
    }

    // Mini drop zones
    const speechDropZone = document.getElementById("speech-drop-zone");
    const musicDropZone = document.getElementById("music-drop-zone");

    [speechDropZone, musicDropZone].forEach(zone => {
        ["dragenter", "dragover"].forEach(evt => {
            zone.addEventListener(evt, e => {
                e.preventDefault();
                zone.classList.add("drag-over");
            });
        });
        ["dragleave", "drop"].forEach(evt => {
            zone.addEventListener(evt, e => {
                e.preventDefault();
                zone.classList.remove("drag-over");
            });
        });
    });

    speechDropZone.addEventListener("drop", e => {
        const dt = new DataTransfer();
        dt.items.add(e.dataTransfer.files[0]);
        speechInput.files = dt.files;
        speechFilename.textContent = e.dataTransfer.files[0].name;
        updateMixButton();
    });

    musicDropZone.addEventListener("drop", e => {
        const dt = new DataTransfer();
        dt.items.add(e.dataTransfer.files[0]);
        musicInput.files = dt.files;
        musicFilename.textContent = e.dataTransfer.files[0].name;
        updateMixButton();
    });

    btnMix.addEventListener("click", async () => {
        mixerResultSection.classList.add("hidden");
        mixerProgressSection.classList.remove("hidden");
        mixerProgressText.textContent = "Mische Audio...";
        btnMix.disabled = true;

        try {
            const formData = new FormData();
            formData.append("speech", speechInput.files[0]);
            formData.append("music", musicInput.files[0]);
            formData.append("music_volume", musicVolume.value);

            const res = await fetch("/api/mix", {
                method: "POST",
                body: formData,
            });
            const result = await res.json();

            if (result.error) throw new Error(result.error);

            mixerFilename = result.filename;
            const sizeMB = (result.size_bytes / 1024 / 1024).toFixed(1);
            mixerResultInfo.textContent = `${result.filename} (${sizeMB} MB)`;
            mixerAudioPlayer.src = `/api/download/${result.filename}`;

            setTimeout(() => {
                mixerProgressSection.classList.add("hidden");
                mixerResultSection.classList.remove("hidden");
            }, 400);
        } catch (err) {
            mixerProgressSection.classList.add("hidden");
            showError(err.message);
        } finally {
            updateMixButton();
        }
    });

    btnMixerDownload.addEventListener("click", () => {
        if (mixerFilename) {
            window.location.href = `/api/download/${mixerFilename}`;
        }
    });

    // --- Error Toast ---
    function showError(message) {
        toastMessage.textContent = message;
        errorToast.classList.remove("hidden");
        errorToast.classList.add("visible");

        setTimeout(() => {
            errorToast.classList.remove("visible");
            setTimeout(() => errorToast.classList.add("hidden"), 400);
        }, 5000);
    }
});
