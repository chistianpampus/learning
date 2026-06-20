# Text-to-Speech Toolkit

Konvertiere Text in natürlich klingende MP3-Dateien mit der [ElevenLabs](https://elevenlabs.io/) API – ideal zum Anhören beim Spazierengehen.

## Features

- 🎙️ **Text-to-Speech** mit ElevenLabs `eleven_multilingual_v2` (Stimme: Christian)
- 🌐 **Web-UI** mit Premium Dark-Mode Design
- 💻 **CLI-Tool** für externen Aufruf und Automatisierung
- 🧹 **Optionaler Präprozessor** – entfernt Code, Markdown-Syntax, URLs etc.
- 🎧 **Audio Mixer** – überlagert Sprache mit Hintergrundmusik
- 📄 **Datei-Support** – `.txt`, `.md`, `.pdf`
- ✂️ **Automatisches Chunking** für lange Texte

## Setup

### 1. Voraussetzungen

- Python 3.10+
- FFmpeg (`brew install ffmpeg`)
- ElevenLabs API-Key ([hier erstellen](https://elevenlabs.io/))

### 2. Installation

```bash
cd text-to-speech
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. API-Key konfigurieren

```bash
cp .env.example .env
# .env bearbeiten und ELEVENLABS_API_KEY eintragen
```

## Nutzung

### Web-UI

```bash
source venv/bin/activate
python app.py
# → http://localhost:5000
```

### CLI

```bash
source venv/bin/activate

# Text direkt konvertieren
python tts_cli.py "Hallo, dies ist ein Test."

# Datei konvertieren
python tts_cli.py --file artikel.txt

# Markdown mit Präprozessor
python tts_cli.py --file README.md --preprocess

# Mehrere Dateien
python tts_cli.py --file kapitel1.txt kapitel2.txt

# Ausgabedatei benennen
python tts_cli.py "Text..." --output mein_audio.mp3

# Verfügbare Stimmen auflisten
python tts_cli.py --list-voices
```

### Audio Mixer

```bash
source venv/bin/activate

# Sprache + Musik mischen
python audio_mixer.py --speech output/rede.mp3 --music hintergrund.mp3

# Mit angepasster Lautstärke
python audio_mixer.py -s rede.mp3 -m musik.mp3 -o mixed.mp3 --music-volume -12
```

## Projektstruktur

```
text-to-speech/
├── config.py               # Zentrale Konfiguration
├── text_preprocessor.py    # Text-Bereinigung für Vorlesen
├── tts_engine.py           # Kern: Text → MP3
├── tts_cli.py              # CLI-Tool
├── audio_mixer.py          # Sprache + Musik mischen
├── app.py                  # Flask Web-Server
├── templates/index.html    # Web-UI
├── static/                 # CSS + JS
├── output/                 # Generierte MP3s
└── requirements.txt        # Dependencies
```

## Präprozessor

Der optionale Präprozessor bereitet Text für natürliches Vorlesen auf:

| Was | Beispiel |
|-----|---------|
| Code entfernen | `` `print("hi")` `` → *(entfernt)* |
| Markdown → Text | `## Kapitel` → `Kapitel` |
| Links auflösen | `[Google](url)` → `Google` |
| Tabellen → Fließtext | Tabellenzeilen → Sätze |
| Abkürzungen | `z.B.` → `zum Beispiel` |
| Sonderzeichen | `>=` → `größer oder gleich` |
