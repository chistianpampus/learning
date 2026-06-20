# Architektur – Text-to-Speech Toolkit

## Überblick

Das TTS-Toolkit wandelt Text in natürlich klingende MP3-Dateien um. Es besteht aus fünf Modulen, die unabhängig voneinander nutzbar sind, aber aufeinander aufbauen.

```mermaid
graph LR
    subgraph Eingabe
        CLI["tts_cli.py<br/>Kommandozeile"]
        WEB["app.py<br/>Web-UI"]
    end

    subgraph Verarbeitung
        PP["text_preprocessor.py<br/>Textbereinigung"]
        EN["tts_engine.py<br/>TTS Engine"]
    end

    subgraph Extern
        API["ElevenLabs API<br/>eleven_multilingual_v2"]
    end

    subgraph Audio
        MIX["audio_mixer.py<br/>Audio Mixer"]
    end

    CLI --> PP
    WEB --> PP
    PP --> EN
    EN --> API
    API --> EN
    WEB --> MIX

    style API fill:#7c3aed,color:#fff
```

## Modulübersicht

### 1. config.py – Konfiguration

Zentrale Stelle für alle Einstellungen. Lädt Werte aus `.env` und stellt Defaults bereit.

```mermaid
graph TD
    ENV[".env Datei"] -->|load_dotenv| CFG["config.py"]
    CFG -->|API_KEY| EN["tts_engine.py"]
    CFG -->|VOICE_ID, MODEL| EN
    CFG -->|OUTPUT_DIR| EN
    CFG -->|MAX_CHUNK_SIZE| EN
    CFG -->|FLASK_*| APP["app.py"]
    CFG -->|ALLOWED_EXTENSIONS| APP
```

| Variable | Default | Beschreibung |
|----------|---------|-------------|
| `ELEVENLABS_API_KEY` | *(aus .env)* | API-Schlüssel |
| `DEFAULT_VOICE_ID` | `NBqeXKdZHweef6y0B67V` | Stimme „Christian" |
| `DEFAULT_MODEL` | `eleven_multilingual_v2` | TTS-Modell |
| `OUTPUT_FORMAT` | `mp3_44100_128` | Audio-Qualität |
| `MAX_CHUNK_SIZE` | `9500` | Zeichen pro API-Aufruf |
| `OUTPUT_DIR` | `output/` | Ausgabeverzeichnis |
| `PREPROCESS_DEFAULT` | `False` | Präprozessor standardmäßig aus |

---

### 2. text_preprocessor.py – Textbereinigung

Optionales Modul, das Text vor der Vertonung für natürliches Vorlesen aufbereitet. Jeder Schritt ist eine eigene Methode der Klasse `TextPreprocessor`.

```mermaid
graph TD
    INPUT["Eingabetext"] --> DETECT["_detect_format()<br/>auto / md / txt / pdf"]
    DETECT --> HTML["_remove_html_tags()"]
    HTML --> CODE["_remove_code_blocks()"]
    CODE --> INLINE["_remove_inline_code()"]

    subgraph "Nur bei Markdown"
        INLINE --> LINKS["_resolve_links()"]
        LINKS --> IMGS["_remove_images()"]
        IMGS --> TABLES["_convert_tables_to_text()"]
        TABLES --> LISTS["_flatten_lists()"]
        LISTS --> MD["_remove_markdown_syntax()"]
    end

    MD --> ABBR["_resolve_abbreviations()<br/>z.B. → zum Beispiel"]
    INLINE -->|"bei txt"| ABBR
    ABBR --> SPECIAL["_resolve_special_chars()<br/>≥ → größer oder gleich"]
    SPECIAL --> CTRL["_remove_control_chars()"]
    CTRL --> NORM["_normalize_whitespace()"]
    NORM --> OUTPUT["Bereinigter Text"]

    style OUTPUT fill:#10b981,color:#fff
```

**Design-Prinzip**: Einzelne Schritte können übersprungen werden, indem der `source_format`-Parameter gesetzt wird. Bei `"txt"` werden Markdown-spezifische Schritte nicht ausgeführt.

---

### 3. tts_engine.py – TTS Engine

Das Herzstück: Nimmt Text entgegen und liefert eine MP3-Datei.

```mermaid
sequenceDiagram
    participant Caller as CLI / Web-UI
    participant Engine as TextToSpeech
    participant PP as TextPreprocessor
    participant API as ElevenLabs API
    participant Pydub as pydub

    Caller->>Engine: convert_text(text, preprocess=True)

    opt preprocess=True
        Engine->>PP: preprocess(text)
        PP-->>Engine: bereinigter Text
    end

    Engine->>Engine: _chunk_text(text, max=9500)

    loop Für jeden Chunk
        Engine->>API: text_to_speech.convert(chunk)
        API-->>Engine: Audio-Bytes (MP3)
    end

    alt Mehrere Chunks
        Engine->>Pydub: Chunks zusammenfügen
        Pydub-->>Engine: Kombinierte MP3
    end

    Engine-->>Caller: Path zur MP3-Datei
```

**Chunking-Algorithmus** – Priorität der Trennstellen:

1. Absatzende (`\n\n`) – bevorzugt ab 50% der Chunk-Größe
2. Satzende (`. `, `! `, `? `) – ab 30%
3. Zeilenende (`\n`) – ab 30%
4. Komma/Semikolon – ab 30%
5. Wortgrenze (Leerzeichen) – Fallback
6. Harte Grenze bei `MAX_CHUNK_SIZE` – letzter Fallback

---

### 4. tts_cli.py – Kommandozeilen-Tool

Wrapper um `tts_engine.py` mit `argparse`. Unterstützt drei Eingabemodi:

```mermaid
graph TD
    A["python tts_cli.py"] --> B{Eingabemodus?}
    B -->|"Argument"| C["Direkter Text<br/>'Hallo Welt'"]
    B -->|"--file"| D["Datei(en) lesen<br/>.txt .md .pdf"]
    B -->|"stdin"| E["Piped Input<br/>cat text.txt ❘ python tts_cli.py"]
    B -->|"--list-voices"| F["Stimmen anzeigen"]

    C --> G["TextToSpeech.convert_text()"]
    D --> G
    E --> G
    G --> H["output/*.mp3"]

    style H fill:#10b981,color:#fff
```

---

### 5. audio_mixer.py – Audio Mixer

Überlagert eine Sprach-MP3 mit einer Musik-MP3 mittels `pydub`.

```mermaid
graph TD
    S["Sprach-MP3"] -->|AudioSegment.from_mp3| SA["Speech Segment"]
    M["Musik-MP3"] -->|AudioSegment.from_mp3| MA["Music Segment"]

    MA -->|"+ music_volume_db"| VOL["Lautstärke anpassen<br/>Standard: -15 dB"]

    VOL --> LOOP{Musik kürzer<br/>als Sprache?}
    LOOP -->|Ja| REP["music * n<br/>Auto-Loop"]
    LOOP -->|Nein| TRIM["Auf Sprachlänge<br/>zuschneiden"]
    REP --> TRIM

    TRIM --> FADE["fade_in() + fade_out()<br/>2s / 3s"]
    FADE --> MIX["speech.overlay(music)"]
    SA --> MIX

    MIX --> OUT["Gemischte MP3<br/>output/mixed_*.mp3"]

    style OUT fill:#10b981,color:#fff
```

---

### 6. app.py – Flask Web-Server

REST-API mit 6 Endpoints, die alle Module orchestriert:

```mermaid
graph TD
    subgraph "Flask Server (Port 5000)"
        R1["GET /<br/>Web-UI anzeigen"]
        R2["POST /api/convert<br/>Text → MP3"]
        R3["POST /api/upload<br/>Dateien → MP3"]
        R4["GET /api/voices<br/>Stimmen laden"]
        R5["POST /api/preprocess<br/>Vorschau"]
        R6["POST /api/mix<br/>Audio mischen"]
        R7["GET /api/download/:file<br/>MP3 herunterladen"]
    end

    R2 --> TTS["tts_engine.py"]
    R3 --> TTS
    R4 --> TTS
    R5 --> PP["text_preprocessor.py"]
    R6 --> MIX["audio_mixer.py"]
    R7 --> FS["output/"]

    style R1 fill:#7c3aed,color:#fff
```

**Request-Flow für Text-Konvertierung:**

```mermaid
sequenceDiagram
    participant Browser
    participant Flask as app.py
    participant Engine as tts_engine.py
    participant API as ElevenLabs

    Browser->>Flask: POST /api/convert {text, voice_id, preprocess}
    Flask->>Engine: convert_text(text, preprocess)
    Engine->>API: text_to_speech.convert()
    API-->>Engine: Audio-Bytes
    Engine-->>Flask: Path zur MP3
    Flask-->>Browser: {filename, size_bytes}

    Browser->>Flask: GET /api/download/tts_*.mp3
    Flask-->>Browser: MP3-Datei
```

---

## Datenfluss

```mermaid
graph TB
    subgraph "Eingabe"
        T["Text"]
        F["Datei (.txt .md .pdf)"]
        S["Sprach-MP3"]
        M["Musik-MP3"]
    end

    subgraph "Verarbeitung"
        PP["Präprozessor<br/>(optional)"]
        CH["Chunking<br/>(≤ 9.500 Zeichen)"]
        EL["ElevenLabs API"]
        AS["Audio Assembly<br/>(pydub)"]
        MX["Audio Mixing<br/>(pydub)"]
    end

    subgraph "Ausgabe"
        O1["output/tts_*.mp3<br/>Vertonter Text"]
        O2["output/mixed_*.mp3<br/>Text + Musik"]
    end

    T --> PP --> CH
    F -->|"read_file_content()"| PP
    CH -->|"Chunk 1..n"| EL
    EL -->|"Audio-Bytes"| AS
    AS --> O1

    S --> MX
    M --> MX
    MX --> O2

    style O1 fill:#10b981,color:#fff
    style O2 fill:#06b6d4,color:#fff
```

---

## Verzeichnisstruktur

```
text-to-speech/
├── config.py               ← Konfiguration (lädt .env)
├── text_preprocessor.py    ← Textbereinigung (10 Schritte)
├── tts_engine.py           ← Kern: Chunking + ElevenLabs API
├── tts_cli.py              ← CLI-Wrapper
├── audio_mixer.py          ← Sprache + Musik mischen
├── app.py                  ← Flask Web-Server
│
├── templates/
│   └── index.html          ← Single-Page Web-UI
├── static/
│   ├── css/style.css       ← Dark-Mode Design
│   └── js/app.js           ← Frontend-Logik
│
├── output/                 ← Generierte MP3s (gitignored)
├── uploads/                ← Temporäre Uploads (gitignored)
│
├── .env                    ← API-Key (gitignored)
├── .env.example            ← Vorlage
├── requirements.txt        ← Dependencies
├── .gitignore
└── README.md
```

## Abhängigkeiten

```mermaid
graph LR
    TTS["tts_engine.py"] --> EL["elevenlabs SDK"]
    TTS --> PD["pydub"]
    TTS --> PP["text_preprocessor.py"]
    TTS --> CFG["config.py"]

    CLI["tts_cli.py"] --> TTS
    CLI --> CFG

    APP["app.py"] --> TTS
    APP --> PP
    APP --> MIX["audio_mixer.py"]
    APP --> FL["Flask"]
    APP --> CFG

    MIX --> PD
    MIX --> CFG

    CFG --> DOT["python-dotenv"]

    PD --> FF["FFmpeg (System)"]
    EL --> API["ElevenLabs API"]

    style API fill:#7c3aed,color:#fff
    style FF fill:#f59e0b,color:#000
```
