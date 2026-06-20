#!/usr/bin/env python3
"""
Flask Web-Server für das Text-to-Speech Toolkit.

Stellt eine Web-Oberfläche bereit zum:
- Text eingeben oder Dateien hochladen → MP3 generieren
- Audio-Mixer: Sprache + Musik überlagern
- Verfügbare Stimmen auflisten

Starten: python app.py
"""

import json
import os
import time
import traceback
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_file

import config
from tts_engine import TextToSpeech, read_file_content
from text_preprocessor import preprocess as preprocess_text
from audio_mixer import mix_audio

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB max upload


@app.route("/")
def index():
    """Web-UI anzeigen."""
    return render_template("index.html")


@app.route("/api/voices", methods=["GET"])
def get_voices():
    """Verfügbare Stimmen laden."""
    try:
        tts = TextToSpeech()
        voices = tts.list_voices()
        return jsonify({
            "voices": voices,
            "default_voice_id": config.DEFAULT_VOICE_ID,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/convert", methods=["POST"])
def convert_text():
    """Text → MP3 konvertieren."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Keine Daten empfangen"}), 400

        text = data.get("text", "").strip()
        if not text:
            return jsonify({"error": "Kein Text vorhanden"}), 400

        voice_id = data.get("voice_id", config.DEFAULT_VOICE_ID)
        do_preprocess = data.get("preprocess", False)

        tts = TextToSpeech(voice_id=voice_id)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = config.OUTPUT_DIR / f"tts_{timestamp}.mp3"

        tts.convert_text(
            text=text,
            output_path=str(output_path),
            preprocess=do_preprocess,
            source_format="auto",
        )

        return jsonify({
            "success": True,
            "filename": output_path.name,
            "size_bytes": output_path.stat().st_size,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
def upload_files():
    """Datei(en) hochladen und konvertieren."""
    try:
        if "files" not in request.files:
            return jsonify({"error": "Keine Dateien hochgeladen"}), 400

        files = request.files.getlist("files")
        voice_id = request.form.get("voice_id", config.DEFAULT_VOICE_ID)
        do_preprocess = request.form.get("preprocess", "false").lower() == "true"

        combined_text = ""
        source_format = "auto"

        for file in files:
            if not file.filename:
                continue

            suffix = Path(file.filename).suffix.lower()
            if suffix not in config.ALLOWED_EXTENSIONS:
                return jsonify({"error": f"Nicht unterstütztes Format: {suffix}"}), 400

            # Datei temporär speichern
            temp_path = config.UPLOAD_DIR / file.filename
            file.save(str(temp_path))

            try:
                text, fmt = read_file_content(str(temp_path))
                combined_text += text + "\n\n"
                source_format = fmt
            finally:
                # Temporäre Datei entfernen
                temp_path.unlink(missing_ok=True)

        if not combined_text.strip():
            return jsonify({"error": "Kein Text in den Dateien gefunden"}), 400

        tts = TextToSpeech(voice_id=voice_id)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = config.OUTPUT_DIR / f"tts_{timestamp}.mp3"

        tts.convert_text(
            text=combined_text,
            output_path=str(output_path),
            preprocess=do_preprocess,
            source_format=source_format,
        )

        return jsonify({
            "success": True,
            "filename": output_path.name,
            "size_bytes": output_path.stat().st_size,
            "char_count": len(combined_text),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/preprocess", methods=["POST"])
def preview_preprocess():
    """Vorschau: Text nach Vorverarbeitung anzeigen."""
    try:
        data = request.get_json()
        text = data.get("text", "")
        source_format = data.get("source_format", "auto")

        processed = preprocess_text(text, source_format)

        return jsonify({
            "original_length": len(text),
            "processed_length": len(processed),
            "processed_text": processed,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mix", methods=["POST"])
def mix_audio_endpoint():
    """Sprach-MP3 + Musik-MP3 mischen."""
    try:
        if "speech" not in request.files or "music" not in request.files:
            return jsonify({"error": "Sprach- und Musik-Datei erforderlich"}), 400

        speech_file = request.files["speech"]
        music_file = request.files["music"]
        music_volume = float(request.form.get("music_volume", -15))

        # Dateien temporär speichern
        speech_path = config.UPLOAD_DIR / f"speech_{int(time.time())}.mp3"
        music_path = config.UPLOAD_DIR / f"music_{int(time.time())}.mp3"

        speech_file.save(str(speech_path))
        music_file.save(str(music_path))

        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = config.OUTPUT_DIR / f"mixed_{timestamp}.mp3"

            mix_audio(
                speech_path=str(speech_path),
                music_path=str(music_path),
                output_path=str(output_path),
                music_volume_db=music_volume,
            )

            return jsonify({
                "success": True,
                "filename": output_path.name,
                "size_bytes": output_path.stat().st_size,
            })
        finally:
            # Temporäre Dateien entfernen
            speech_path.unlink(missing_ok=True)
            music_path.unlink(missing_ok=True)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<filename>")
def download_file(filename):
    """Generierte MP3 herunterladen."""
    file_path = config.OUTPUT_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "Datei nicht gefunden"}), 404
    return send_file(str(file_path), as_attachment=True, download_name=filename)


if __name__ == "__main__":
    print(f"\n🎙️  Text-to-Speech Toolkit")
    print(f"   Server: http://localhost:{config.FLASK_PORT}")
    print(f"   Voice:  {config.DEFAULT_VOICE_ID}")
    print(f"   Output: {config.OUTPUT_DIR}\n")

    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
    )
