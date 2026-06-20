#!/usr/bin/env python3
"""
Audio Mixer – Überlagert Sprache mit Hintergrundmusik.

Nimmt eine Sprach-MP3 und eine Musik-MP3 als Input und erzeugt
eine gemischte MP3, bei der die Musik unter der Sprache liegt.

Nutzung:
    python audio_mixer.py --speech output/rede.mp3 --music hintergrund.mp3
    python audio_mixer.py --speech rede.mp3 --music musik.mp3 --output mixed.mp3 --music-volume -12
"""

import argparse
import sys
import time
from pathlib import Path

from pydub import AudioSegment

# Projektverzeichnis zum Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

import config


def mix_audio(
    speech_path: str,
    music_path: str,
    output_path: str = None,
    music_volume_db: float = -15.0,
    fade_in_ms: int = 2000,
    fade_out_ms: int = 3000,
) -> Path:
    """
    Überlagert eine Sprach-MP3 mit einer Musik-MP3.

    Args:
        speech_path: Pfad zur Sprach-MP3.
        music_path: Pfad zur Musik-MP3.
        output_path: Pfad für die Ausgabedatei (optional).
        music_volume_db: Lautstärke-Anpassung der Musik in dB (negativ = leiser).
        fade_in_ms: Fade-In der Musik am Anfang in Millisekunden.
        fade_out_ms: Fade-Out der Musik am Ende in Millisekunden.

    Returns:
        Path zur erstellten gemischten MP3-Datei.
    """
    # Dateien laden
    print(f"  📖 Lade Sprache: {speech_path}")
    speech = AudioSegment.from_mp3(speech_path)

    print(f"  🎵 Lade Musik: {music_path}")
    music = AudioSegment.from_mp3(music_path)

    # Musik-Lautstärke anpassen
    music = music + music_volume_db

    # Musik loopen falls kürzer als Sprache
    speech_duration = len(speech)
    music_duration = len(music)

    if music_duration < speech_duration:
        loops_needed = (speech_duration // music_duration) + 1
        print(f"  🔁 Musik wird {loops_needed}x geloopt ({music_duration}ms → {speech_duration}ms)")
        music = music * loops_needed

    # Musik auf Sprach-Länge zuschneiden (+ Fade-Out-Raum)
    target_length = speech_duration + fade_out_ms
    music = music[:target_length]

    # Fade-In und Fade-Out anwenden
    if fade_in_ms > 0:
        music = music.fade_in(fade_in_ms)
    if fade_out_ms > 0:
        music = music.fade_out(fade_out_ms)

    # Überlagern
    print(f"  🎛️  Mische Audio (Musik: {music_volume_db} dB)...")
    mixed = speech.overlay(music, position=0)

    # Ausgabepfad
    if output_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = config.OUTPUT_DIR / f"mixed_{timestamp}.mp3"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Exportieren
    mixed.export(str(output_path), format="mp3", bitrate="128k")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Überlagert eine Sprach-MP3 mit Hintergrundmusik",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s --speech output/rede.mp3 --music hintergrund.mp3
  %(prog)s --speech rede.mp3 --music musik.mp3 --output mixed.mp3 --music-volume -12
  %(prog)s -s rede.mp3 -m musik.mp3 --fade-in 3000 --fade-out 5000
        """,
    )

    parser.add_argument(
        "--speech", "-s",
        required=True,
        help="Pfad zur Sprach-MP3",
    )
    parser.add_argument(
        "--music", "-m",
        required=True,
        help="Pfad zur Musik-MP3",
    )
    parser.add_argument(
        "--output", "-o",
        help="Ausgabedatei (Standard: output/mixed_TIMESTAMP.mp3)",
    )
    parser.add_argument(
        "--music-volume",
        type=float,
        default=-15.0,
        help="Musik-Lautstärke in dB relativ zur Sprache (Standard: -15)",
    )
    parser.add_argument(
        "--fade-in",
        type=int,
        default=2000,
        help="Musik Fade-In in Millisekunden (Standard: 2000)",
    )
    parser.add_argument(
        "--fade-out",
        type=int,
        default=3000,
        help="Musik Fade-Out in Millisekunden (Standard: 3000)",
    )

    args = parser.parse_args()

    # Dateien prüfen
    for label, path in [("Sprache", args.speech), ("Musik", args.music)]:
        if not Path(path).exists():
            print(f"❌ {label}-Datei nicht gefunden: {path}", file=sys.stderr)
            sys.exit(1)

    print(f"\n🎧 Audio Mixer\n")

    try:
        output_path = mix_audio(
            speech_path=args.speech,
            music_path=args.music,
            output_path=args.output,
            music_volume_db=args.music_volume,
            fade_in_ms=args.fade_in,
            fade_out_ms=args.fade_out,
        )

        size_mb = output_path.stat().st_size / (1024 * 1024)
        duration_s = len(AudioSegment.from_mp3(str(output_path))) / 1000
        minutes = int(duration_s // 60)
        seconds = int(duration_s % 60)

        print(f"\n✅ Gemischte MP3 erstellt: {output_path}")
        print(f"   Größe: {size_mb:.1f} MB")
        print(f"   Dauer: {minutes}:{seconds:02d}")

    except Exception as e:
        print(f"\n❌ Fehler beim Mischen: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
