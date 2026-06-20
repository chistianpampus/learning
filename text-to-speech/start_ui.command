#!/bin/bash
# ============================================
# Text-to-Speech Web-UI starten
# Doppelklick im Finder oder im Terminal ausführen
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎙️  Text-to-Speech Web-UI"
echo "========================="
echo ""

# Python-Umgebung aktivieren
if [ ! -d "venv" ]; then
    echo "❌ Virtuelle Umgebung nicht gefunden."
    echo "   Bitte zuerst einrichten:"
    echo "   python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    echo ""
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi

source venv/bin/activate

# .env prüfen
if [ ! -f ".env" ]; then
    echo "⚠️  Keine .env Datei gefunden."
    echo "   Kopiere .env.example nach .env und trage deinen API-Key ein:"
    echo "   cp .env.example .env"
    echo ""
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi

# Browser öffnen (nach kurzer Wartezeit)
(sleep 2 && open "http://localhost:5050") &

echo "🌐 Öffne http://localhost:5050 ..."
echo "   Zum Beenden: Ctrl+C"
echo ""

python app.py
