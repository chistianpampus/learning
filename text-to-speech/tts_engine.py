"""
TTS Engine – Kern-Modul für Text-to-Speech Konvertierung.

Verwendet die ElevenLabs API (eleven_multilingual_v2) um Text in natürlich
klingende MP3-Dateien umzuwandeln. Unterstützt automatisches Chunking
für lange Texte und optionale Vorverarbeitung.
"""

import io
import os
import re
import time
from pathlib import Path
from typing import Generator, Optional

from pydub import AudioSegment

import config
from text_preprocessor import preprocess as preprocess_text


class TextToSpeech:
    """Konvertiert Text in MP3-Dateien via ElevenLabs API."""

    def __init__(
        self,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        output_format: Optional[str] = None,
    ):
        """
        Initialisiert die TTS Engine.

        Args:
            voice_id: ElevenLabs Voice-ID (Standard: aus config).
            model_id: ElevenLabs Modell-ID (Standard: eleven_multilingual_v2).
            output_format: Audio-Ausgabeformat (Standard: mp3_44100_128).
        """
        from elevenlabs.client import ElevenLabs

        if not config.ELEVENLABS_API_KEY:
            raise ValueError(
                "ELEVENLABS_API_KEY nicht gesetzt. "
                "Bitte in .env-Datei hinterlegen oder als Umgebungsvariable setzen."
            )

        self.client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
        self.voice_id = voice_id or config.DEFAULT_VOICE_ID
        self.model_id = model_id or config.DEFAULT_MODEL
        self.output_format = output_format or config.OUTPUT_FORMAT

    def convert_text(
        self,
        text: str,
        output_path: Optional[str] = None,
        preprocess: bool = False,
        source_format: str = "auto",
        progress_callback=None,
    ) -> Path:
        """
        Konvertiert Text in eine MP3-Datei.

        Args:
            text: Der zu konvertierende Text.
            output_path: Pfad für die Ausgabedatei (optional, wird generiert).
            preprocess: Ob der Text vorverarbeitet werden soll.
            source_format: Quellformat für den Präprozessor ("txt", "md", "pdf", "auto").
            progress_callback: Optionale Callback-Funktion für Fortschrittsmeldungen.
                               Signatur: callback(current_chunk, total_chunks, status_message)

        Returns:
            Path zur erstellten MP3-Datei.
        """
        if not text or not text.strip():
            raise ValueError("Kein Text zum Konvertieren vorhanden.")

        # Optional: Text vorverarbeiten
        if preprocess:
            text = preprocess_text(text, source_format)
            if not text.strip():
                raise ValueError("Nach der Vorverarbeitung ist kein Text übrig.")

        # Ausgabepfad generieren
        if output_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = config.OUTPUT_DIR / f"tts_{timestamp}.mp3"
        else:
            output_path = Path(output_path)

        # Verzeichnis erstellen
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Text in Chunks aufteilen
        chunks = self._chunk_text(text)

        if len(chunks) == 1:
            # Einzelner Chunk – direkt speichern
            if progress_callback:
                progress_callback(1, 1, "Generiere Audio...")
            audio_data = self._generate_chunk(chunks[0])
            with open(output_path, "wb") as f:
                for chunk_bytes in audio_data:
                    f.write(chunk_bytes)
            if progress_callback:
                progress_callback(1, 1, "Fertig!")
        else:
            # Mehrere Chunks – einzeln generieren und zusammenfügen
            audio_segments = []
            for i, chunk in enumerate(chunks):
                if progress_callback:
                    progress_callback(i + 1, len(chunks), f"Chunk {i + 1}/{len(chunks)}...")

                audio_data = self._generate_chunk(chunk)
                # Bytes sammeln
                audio_bytes = b""
                for chunk_bytes in audio_data:
                    audio_bytes += chunk_bytes

                # In AudioSegment konvertieren
                segment = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
                audio_segments.append(segment)

            # Zusammenfügen
            if progress_callback:
                progress_callback(len(chunks), len(chunks), "Füge Chunks zusammen...")

            combined = audio_segments[0]
            for segment in audio_segments[1:]:
                combined += segment

            combined.export(str(output_path), format="mp3", bitrate="128k")

            if progress_callback:
                progress_callback(len(chunks), len(chunks), "Fertig!")

        return output_path

    def _chunk_text(self, text: str, max_chars: Optional[int] = None) -> list[str]:
        """
        Teilt langen Text in Chunks auf, die das API-Limit nicht überschreiten.
        Splittet bevorzugt an Satzgrenzen.

        Args:
            text: Der aufzuteilende Text.
            max_chars: Maximale Zeichenzahl pro Chunk (Standard: aus config).

        Returns:
            Liste von Text-Chunks.
        """
        max_chars = max_chars or config.MAX_CHUNK_SIZE

        if len(text) <= max_chars:
            return [text]

        chunks = []
        remaining = text

        while remaining:
            if len(remaining) <= max_chars:
                chunks.append(remaining)
                break

            # Finde die beste Trennstelle innerhalb des Limits
            split_pos = self._find_split_position(remaining, max_chars)
            chunks.append(remaining[:split_pos].strip())
            remaining = remaining[split_pos:].strip()

        return [c for c in chunks if c]  # Leere Chunks entfernen

    def _find_split_position(self, text: str, max_pos: int) -> int:
        """Findet die beste Stelle zum Aufteilen des Texts."""
        search_text = text[:max_pos]

        # Priorität 1: Absatzende (\n\n)
        last_para = search_text.rfind("\n\n")
        if last_para > max_pos * 0.5:
            return last_para + 2

        # Priorität 2: Satzende (. ! ?)
        for sep in [". ", "! ", "? "]:
            last_sep = search_text.rfind(sep)
            if last_sep > max_pos * 0.3:
                return last_sep + len(sep)

        # Priorität 3: Zeilenende
        last_newline = search_text.rfind("\n")
        if last_newline > max_pos * 0.3:
            return last_newline + 1

        # Priorität 4: Komma oder Semikolon
        for sep in [", ", "; "]:
            last_sep = search_text.rfind(sep)
            if last_sep > max_pos * 0.3:
                return last_sep + len(sep)

        # Fallback: An Wortgrenze
        last_space = search_text.rfind(" ")
        if last_space > 0:
            return last_space + 1

        # Letzter Fallback: Harte Grenze
        return max_pos

    def _generate_chunk(self, text: str) -> Generator:
        """
        Generiert Audio für einen einzelnen Text-Chunk via ElevenLabs API.

        Args:
            text: Der zu vertonende Text-Chunk.

        Returns:
            Generator mit Audio-Bytes.
        """
        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id=self.voice_id,
            model_id=self.model_id,
            output_format=self.output_format,
        )
        return audio

    def list_voices(self) -> list[dict]:
        """
        Ruft alle verfügbaren Stimmen aus dem ElevenLabs-Account ab.

        Returns:
            Liste von Dicts mit voice_id, name und weiteren Infos.
        """
        response = self.client.voices.get_all()
        voices = []
        for voice in response.voices:
            voices.append({
                "voice_id": voice.voice_id,
                "name": voice.name,
                "category": getattr(voice, "category", "unknown"),
                "labels": getattr(voice, "labels", {}),
            })
        return voices


def read_file_content(file_path: str) -> tuple[str, str]:
    """
    Liest den Textinhalt einer Datei (.txt, .md, .pdf).

    Args:
        file_path: Pfad zur Datei.

    Returns:
        Tuple aus (text_content, detected_format).
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix not in config.ALLOWED_EXTENSIONS:
        raise ValueError(f"Nicht unterstütztes Dateiformat: {suffix}")

    if suffix == ".pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(path))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            return text, "pdf"
        except ImportError:
            raise ImportError("PyPDF2 wird benötigt für PDF-Dateien: pip install PyPDF2")
    else:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return text, "md" if suffix == ".md" else "txt"
