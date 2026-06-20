"""
Zentrale Konfiguration für das Text-to-Speech Toolkit.
Lädt Einstellungen aus der .env-Datei und stellt Standardwerte bereit.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env laden
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# ElevenLabs API
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
DEFAULT_VOICE_ID = os.getenv("DEFAULT_VOICE_ID", "NBqeXKdZHweef6y0B67V")  # Christian
DEFAULT_MODEL = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"

# Chunking
MAX_CHUNK_SIZE = 9500  # Zeichen pro API-Aufruf (Limit: 10.000)

# Ausgabe
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Upload
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Präprozessor
PREPROCESS_DEFAULT = False

# Flask
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True

# Erlaubte Dateiendungen für Upload
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}
