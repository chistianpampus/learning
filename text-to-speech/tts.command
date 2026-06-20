#!/bin/bash
# ============================================
# Text-to-Speech CLI Shortcut
# Nutzung: ./tts.command "Text zum Vorlesen"
#          ./tts.command --file datei.md --preprocess
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Python-Umgebung aktivieren
if [ ! -d "venv" ]; then
    echo "❌ Virtuelle Umgebung nicht gefunden."
    echo "   python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate

if [ ! -f ".env" ]; then
    echo "⚠️  Keine .env Datei. Kopiere .env.example nach .env und trage deinen API-Key ein."
    exit 1
fi

# Alle Argumente an das CLI-Tool weiterleiten
python tts_cli.py "$@"
