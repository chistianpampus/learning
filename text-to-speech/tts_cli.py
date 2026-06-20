#!/usr/bin/env python3
"""
CLI-Tool für Text-to-Speech Konvertierung.

Nutzung:
    python tts_cli.py "Text zum Vorlesen"
    python tts_cli.py --file artikel.txt
    python tts_cli.py --file kapitel1.md --preprocess
    python tts_cli.py --list-voices
"""

import argparse
import sys
from pathlib import Path

# Projektverzeichnis zum Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

import config
from tts_engine import TextToSpeech, read_file_content


def progress_callback(current: int, total: int, message: str):
    """Zeigt Fortschritt in der Konsole an."""
    bar_length = 30
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\r  [{bar}] {current}/{total} – {message}", end="", flush=True)
    if current == total and "Fertig" in message:
        print()  # Neue Zeile am Ende


def main():
    parser = argparse.ArgumentParser(
        description="Text-to-Speech Konvertierung mit ElevenLabs API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s "Hallo, dies ist ein Test."
  %(prog)s --file artikel.txt --output vortrag.mp3
  %(prog)s --file README.md --preprocess
  %(prog)s --list-voices
        """,
    )

    # Hauptargumente
    parser.add_argument(
        "text",
        nargs="?",
        help="Text, der in Sprache umgewandelt werden soll",
    )
    parser.add_argument(
        "--file", "-f",
        nargs="+",
        help="Eine oder mehrere Dateien (.txt, .md, .pdf) als Textquelle",
    )

    # Optionen
    parser.add_argument(
        "--output", "-o",
        help="Ausgabedatei (Standard: output/tts_TIMESTAMP.mp3)",
    )
    parser.add_argument(
        "--voice-id", "-v",
        default=config.DEFAULT_VOICE_ID,
        help=f"ElevenLabs Voice-ID (Standard: {config.DEFAULT_VOICE_ID})",
    )
    parser.add_argument(
        "--preprocess", "-p",
        action="store_true",
        help="Text vor dem Vorlesen bereinigen (Code, Markdown-Syntax etc. entfernen)",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="Alle verfügbaren Stimmen auflisten",
    )

    args = parser.parse_args()

    # Voices auflisten
    if args.list_voices:
        print("🎤 Verfügbare Stimmen:\n")
        try:
            tts = TextToSpeech()
            voices = tts.list_voices()
            for voice in voices:
                marker = " ⭐" if voice["voice_id"] == config.DEFAULT_VOICE_ID else ""
                print(f"  {voice['name']}{marker}")
                print(f"    ID: {voice['voice_id']}")
                if voice.get("labels"):
                    labels = ", ".join(f"{k}: {v}" for k, v in voice["labels"].items())
                    print(f"    Labels: {labels}")
                print()
        except Exception as e:
            print(f"❌ Fehler beim Laden der Stimmen: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Text zusammensetzen
    text = ""
    source_format = "auto"

    if args.file:
        # Dateien lesen
        for file_path in args.file:
            path = Path(file_path)
            if not path.exists():
                print(f"❌ Datei nicht gefunden: {file_path}", file=sys.stderr)
                sys.exit(1)
            try:
                file_text, fmt = read_file_content(str(path))
                text += file_text + "\n\n"
                source_format = fmt
                print(f"📄 Geladen: {path.name} ({len(file_text)} Zeichen, Format: {fmt})")
            except Exception as e:
                print(f"❌ Fehler beim Lesen von {file_path}: {e}", file=sys.stderr)
                sys.exit(1)
    elif args.text:
        text = args.text
    else:
        # Aus stdin lesen
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            parser.print_help()
            sys.exit(1)

    if not text.strip():
        print("❌ Kein Text vorhanden.", file=sys.stderr)
        sys.exit(1)

    # TTS durchführen
    print(f"\n🔊 Starte Konvertierung...")
    print(f"   Stimme: {args.voice_id}")
    print(f"   Zeichen: {len(text)}")
    print(f"   Präprozessor: {'An' if args.preprocess else 'Aus'}")
    print()

    try:
        tts = TextToSpeech(voice_id=args.voice_id)
        output_path = tts.convert_text(
            text=text,
            output_path=args.output,
            preprocess=args.preprocess,
            source_format=source_format,
            progress_callback=progress_callback,
        )
        print(f"\n✅ MP3 erstellt: {output_path}")
        # Dateigröße anzeigen
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"   Größe: {size_mb:.1f} MB")
    except Exception as e:
        print(f"\n❌ Fehler bei der Konvertierung: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
