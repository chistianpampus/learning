# Nutzungsanleitung – Text-to-Speech Toolkit

## Ersteinrichtung (einmalig)

### 1. API-Key einrichten

```bash
cd ~/claude_code/learning/text-to-speech
cp .env.example .env
```

Öffne `.env` und trage deinen ElevenLabs API-Key ein:

```
ELEVENLABS_API_KEY=sk-dein-key-hier
DEFAULT_VOICE_ID=NBqeXKdZHweef6y0B67V
```

> **API-Key erstellen**: [elevenlabs.io](https://elevenlabs.io/) → Login → Developers (unten links) → API Key erstellen

### 2. Python-Umgebung (falls noch nicht geschehen)

```bash
cd ~/claude_code/learning/text-to-speech
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Web-UI starten

### Per Konsole

```bash
cd ~/claude_code/learning/text-to-speech
source venv/bin/activate
python app.py
```

Dann im Browser öffnen: **http://localhost:5050**

### Per Shortcut

Doppelklick auf `start_ui.command` im Finder, oder im Terminal:

```bash
~/claude_code/learning/text-to-speech/start_ui.command
```

> Die Datei `start_ui.command` öffnet automatisch die Web-UI im Browser.

### Was du in der Web-UI machen kannst

**Tab „Text → Sprache":**
1. Text in das Textfeld einfügen **oder** Dateien hochladen (.txt, .md, .pdf)
2. Stimme auswählen (Standard: Christian ⭐)
3. Optional: **Präprozessor** aktivieren – bereinigt Code, Markdown-Syntax, URLs etc.
4. „MP3 generieren" klicken
5. Ergebnis anhören und herunterladen

**Tab „Audio Mixer":**
1. Sprach-MP3 hochladen
2. Musik-MP3 hochladen
3. Musik-Lautstärke mit Slider einstellen
4. „Audio mischen" klicken
5. Ergebnis herunterladen

---

## CLI-Nutzung

### Per Konsole

Immer zuerst das venv aktivieren:

```bash
cd ~/claude_code/learning/text-to-speech
source venv/bin/activate
```

#### Text direkt übergeben

```bash
python tts_cli.py "Das ist ein Beispieltext, der vorgelesen werden soll."
```

#### Datei konvertieren

```bash
python tts_cli.py --file ~/Dokumente/artikel.txt
```

#### Markdown mit Präprozessor (entfernt Code, Formatierung etc.)

```bash
python tts_cli.py --file README.md --preprocess
```

#### Mehrere Dateien zu einer MP3

```bash
python tts_cli.py --file kapitel1.txt kapitel2.txt kapitel3.txt
```

#### Ausgabedatei benennen

```bash
python tts_cli.py "Text..." --output ~/Desktop/mein_audio.mp3
```

#### Text aus der Zwischenablage (macOS)

```bash
pbpaste | python tts_cli.py
```

#### Verfügbare Stimmen anzeigen

```bash
python tts_cli.py --list-voices
```

### Per Shortcut

Du kannst die Shortcut-Skripte direkt verwenden:

```bash
# Text direkt
~/claude_code/learning/text-to-speech/tts.command "Hallo, das ist ein Test."

# Datei konvertieren
~/claude_code/learning/text-to-speech/tts.command --file ~/Dokumente/text.txt

# Mit Präprozessor
~/claude_code/learning/text-to-speech/tts.command --file notes.md --preprocess
```

---

## Audio Mixer (CLI)

```bash
cd ~/claude_code/learning/text-to-speech
source venv/bin/activate

# Standard: Musik -15 dB unter Sprache
python audio_mixer.py --speech output/rede.mp3 --music ~/Musik/hintergrund.mp3

# Musik lauter (-10 dB) mit Ausgabedatei
python audio_mixer.py -s output/rede.mp3 -m musik.mp3 -o ~/Desktop/podcast.mp3 --music-volume -10

# Fade anpassen (3s ein, 5s aus)
python audio_mixer.py -s rede.mp3 -m musik.mp3 --fade-in 3000 --fade-out 5000
```

---

## Shell-Aliase einrichten (optional)

Füge diese Zeilen zu deiner `~/.zshrc` hinzu für noch schnelleren Zugriff:

```bash
# Text-to-Speech Shortcuts
alias tts='cd ~/claude_code/learning/text-to-speech && source venv/bin/activate && python tts_cli.py'
alias tts-ui='cd ~/claude_code/learning/text-to-speech && source venv/bin/activate && python app.py'
alias tts-mix='cd ~/claude_code/learning/text-to-speech && source venv/bin/activate && python audio_mixer.py'
```

Dann `source ~/.zshrc` ausführen. Danach geht:

```bash
tts "Schnell mal was vorlesen lassen."
tts --file artikel.md --preprocess
tts-ui    # Web-UI starten
tts-mix --speech rede.mp3 --music musik.mp3
```

---

## Ausgabedateien

Alle generierten MP3s landen in:

```
~/claude_code/learning/text-to-speech/output/
```

Dateinamen-Schema:
- `tts_20260620_143022.mp3` – Vertonter Text (Zeitstempel)
- `mixed_20260620_143055.mp3` – Gemischtes Audio

---

## Tipps

- **Lange Texte**: Texte über 9.500 Zeichen werden automatisch in Chunks aufgeteilt. Das funktioniert nahtlos.
- **Präprozessor**: Besonders nützlich für Markdown-Dateien und Dokumentationen mit Codeblöcken.
- **Musik-Lautstärke**: `-15 dB` ist ein guter Startwert. Für Podcasts eher `-20 dB`, für Atmosphäre `-10 dB`.
- **Zwischenablage**: Auf macOS `pbpaste | python tts_cli.py` um kopierten Text direkt zu vertonen.
