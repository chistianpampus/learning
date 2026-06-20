"""
Text-Präprozessor für das TTS-Toolkit.

Bereinigt Text vor dem Vorlesen: entfernt Codeblöcke, Markdown-Syntax,
URLs, Steuerzeichen und wandelt den Text in eine vorlesefreundliche Form um.

Jeder Bereinigungsschritt ist eine eigene Methode, sodass einzelne Schritte
leicht aktiviert/deaktiviert oder erweitert werden können.
"""

import re
from typing import Optional


class TextPreprocessor:
    """Bereitet Text für natürliches Vorlesen auf."""

    # Deutsche Abkürzungen → ausgeschriebene Form
    ABBREVIATIONS = {
        "z.B.": "zum Beispiel",
        "z. B.": "zum Beispiel",
        "d.h.": "das heißt",
        "d. h.": "das heißt",
        "u.a.": "unter anderem",
        "u. a.": "unter anderem",
        "o.ä.": "oder ähnliches",
        "o. ä.": "oder ähnliches",
        "s.o.": "siehe oben",
        "s. o.": "siehe oben",
        "s.u.": "siehe unten",
        "s. u.": "siehe unten",
        "i.d.R.": "in der Regel",
        "i. d. R.": "in der Regel",
        "bzgl.": "bezüglich",
        "ggf.": "gegebenenfalls",
        "ca.": "circa",
        "inkl.": "inklusive",
        "exkl.": "exklusive",
        "Nr.": "Nummer",
        "bzw.": "beziehungsweise",
        "usw.": "und so weiter",
        "etc.": "et cetera",
        "evtl.": "eventuell",
        "ggfs.": "gegebenenfalls",
        "gem.": "gemäß",
        "lt.": "laut",
        "v.a.": "vor allem",
        "v. a.": "vor allem",
        "sog.": "sogenannt",
        "u.U.": "unter Umständen",
        "u. U.": "unter Umständen",
        "i.A.": "im Allgemeinen",
        "i. A.": "im Allgemeinen",
        "o.g.": "oben genannt",
        "o. g.": "oben genannt",
    }

    # Sonderzeichen → gesprochene Form
    SPECIAL_CHARS = {
        "→": " ergibt ",
        "←": " kommt von ",
        "↔": " wechselseitig ",
        ">=": " größer oder gleich ",
        "<=": " kleiner oder gleich ",
        "!=": " ungleich ",
        "==": " gleich ",
        "=>": " ergibt ",
        "&&": " und ",
        "||": " oder ",
        "…": "...",
        "–": ", ",
        "—": ", ",
        "&": " und ",
        "%": " Prozent",
        "€": " Euro",
        "$": " Dollar",
        "£": " Pfund",
        "°C": " Grad Celsius",
        "°F": " Grad Fahrenheit",
        "°": " Grad",
    }

    def __init__(self):
        pass

    def preprocess(self, text: str, source_format: str = "auto") -> str:
        """
        Hauptfunktion: Bereinigt den Text für natürliches Vorlesen.

        Args:
            text: Der zu bereinigende Text.
            source_format: "txt", "md", "pdf" oder "auto" (erkennt Format automatisch).

        Returns:
            Bereinigter, vorlesefreundlicher Text.
        """
        if not text or not text.strip():
            return ""

        # Format erkennen
        if source_format == "auto":
            source_format = self._detect_format(text)

        # Bereinigungsschritte der Reihe nach anwenden
        text = self._remove_html_tags(text)
        text = self._remove_code_blocks(text)
        text = self._remove_inline_code(text)

        if source_format in ("md", "auto"):
            text = self._resolve_links(text)
            text = self._remove_images(text)
            text = self._convert_tables_to_text(text)
            text = self._flatten_lists(text)
            text = self._remove_markdown_syntax(text)

        text = self._resolve_abbreviations(text)
        text = self._resolve_special_chars(text)
        text = self._remove_control_chars(text)
        text = self._normalize_whitespace(text)

        return text.strip()

    def _detect_format(self, text: str) -> str:
        """Erkennt ob der Text Markdown-Syntax enthält."""
        markdown_patterns = [
            r"^#{1,6}\s",       # Headings
            r"\*\*\w",          # Bold
            r"```",             # Code blocks
            r"^\s*[-*+]\s",     # Unordered lists
            r"^\s*\d+\.\s",     # Ordered lists
            r"\[.*?\]\(.*?\)",  # Links
        ]
        for pattern in markdown_patterns:
            if re.search(pattern, text, re.MULTILINE):
                return "md"
        return "txt"

    def _remove_code_blocks(self, text: str) -> str:
        """Entfernt Fenced Code Blocks (``` ... ```)."""
        # Multi-line code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        # Indented code blocks (4 Leerzeichen oder Tab am Zeilenanfang, mehrere Zeilen)
        text = re.sub(r"(?m)(^(?:    |\t).+\n?){2,}", "", text)
        return text

    def _remove_inline_code(self, text: str) -> str:
        """Entfernt Inline-Code (`...`)."""
        text = re.sub(r"`[^`]+`", "", text)
        return text

    def _remove_markdown_syntax(self, text: str) -> str:
        """Entfernt Markdown-Formatierungszeichen."""
        # Headings: ## Text → Text
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
        # Bold/Italic: **text** oder *text* → text
        text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        text = re.sub(r"_(.+?)_", r"\1", text)
        # Strikethrough: ~~text~~ → text
        text = re.sub(r"~~(.+?)~~", r"\1", text)
        # Horizontal rules
        text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
        # Blockquotes: > text → text
        text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
        # Alert syntax: > [!NOTE], > [!WARNING] etc.
        text = re.sub(r"^\s*>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$", "", text, flags=re.MULTILINE)
        return text

    def _resolve_links(self, text: str) -> str:
        """Löst Markdown-Links auf: [Text](url) → Text. Entfernt nackte URLs."""
        # [Text](url) → Text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # Nackte URLs entfernen
        text = re.sub(r"https?://\S+", "", text)
        return text

    def _remove_images(self, text: str) -> str:
        """Entfernt Bild-Referenzen: ![alt](url)."""
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)
        return text

    def _convert_tables_to_text(self, text: str) -> str:
        """Wandelt Markdown-Tabellen in lesbaren Fließtext um."""
        lines = text.split("\n")
        result = []
        table_rows = []
        headers = []
        in_table = False

        for line in lines:
            stripped = line.strip()
            # Tabellen-Trennlinie erkennen (|---|---|)
            if re.match(r"^\|?\s*[-:]+[-|\s:]*$", stripped):
                continue

            # Tabellen-Zeile erkennen
            if "|" in stripped and stripped.startswith("|"):
                cells = [c.strip() for c in stripped.split("|") if c.strip()]
                if not in_table:
                    headers = cells
                    in_table = True
                else:
                    table_rows.append(cells)
            else:
                # Tabelle beendet – in Text umwandeln
                if in_table and headers and table_rows:
                    for row in table_rows:
                        parts = []
                        for i, cell in enumerate(row):
                            if i < len(headers):
                                parts.append(f"{headers[i]}: {cell}")
                            else:
                                parts.append(cell)
                        result.append(", ".join(parts) + ".")
                    result.append("")
                    headers = []
                    table_rows = []
                    in_table = False
                elif in_table:
                    in_table = False
                    headers = []
                    table_rows = []

                result.append(line)

        # Falls Tabelle am Ende steht
        if in_table and headers and table_rows:
            for row in table_rows:
                parts = []
                for i, cell in enumerate(row):
                    if i < len(headers):
                        parts.append(f"{headers[i]}: {cell}")
                    else:
                        parts.append(cell)
                result.append(", ".join(parts) + ".")

        return "\n".join(result)

    def _flatten_lists(self, text: str) -> str:
        """Wandelt Aufzählungen in Fließtext um."""
        lines = text.split("\n")
        result = []
        list_items = []
        in_list = False

        for line in lines:
            stripped = line.strip()
            # Ungeordnete Liste: - item, * item, + item
            list_match = re.match(r"^[-*+]\s+(.+)$", stripped)
            # Geordnete Liste: 1. item, 2. item
            if not list_match:
                list_match = re.match(r"^\d+\.\s+(.+)$", stripped)

            if list_match:
                in_list = True
                list_items.append(list_match.group(1))
            else:
                if in_list and list_items:
                    # Kurze Listen kommasepariert, lange als Sätze
                    if len(list_items) <= 5 and all(len(item) < 50 for item in list_items):
                        result.append(", ".join(list_items) + ".")
                    else:
                        for item in list_items:
                            if not item.endswith((".", "!", "?")):
                                item += "."
                            result.append(item)
                    result.append("")
                    list_items = []
                    in_list = False
                result.append(line)

        # Restliche Liste verarbeiten
        if list_items:
            if len(list_items) <= 5 and all(len(item) < 50 for item in list_items):
                result.append(", ".join(list_items) + ".")
            else:
                for item in list_items:
                    if not item.endswith((".", "!", "?")):
                        item += "."
                    result.append(item)

        return "\n".join(result)

    def _remove_html_tags(self, text: str) -> str:
        """Entfernt HTML-Tags, behält den Textinhalt."""
        text = re.sub(r"<br\s*/?>", "\n", text)
        text = re.sub(r"<[^>]+>", "", text)
        return text

    def _resolve_abbreviations(self, text: str) -> str:
        """Ersetzt gängige Abkürzungen durch ausgeschriebene Form."""
        for abbr, full in self.ABBREVIATIONS.items():
            text = text.replace(abbr, full)
        return text

    def _resolve_special_chars(self, text: str) -> str:
        """Ersetzt Sonderzeichen durch gesprochene Form."""
        for char, spoken in self.SPECIAL_CHARS.items():
            text = text.replace(char, spoken)
        return text

    def _remove_control_chars(self, text: str) -> str:
        """Entfernt Steuerzeichen und nicht-druckbare Zeichen."""
        # Tabs durch Leerzeichen ersetzen
        text = text.replace("\t", " ")
        # Carriage Returns entfernen
        text = text.replace("\r", "")
        # Unicode-Steuerzeichen entfernen (außer Newlines)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalisiert Leerzeichen und Zeilenumbrüche."""
        # Mehrfache Leerzeichen → ein Leerzeichen
        text = re.sub(r" {2,}", " ", text)
        # Mehr als 2 aufeinanderfolgende Leerzeilen → maximal 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Leerzeichen am Zeilenanfang/-ende entfernen
        text = "\n".join(line.strip() for line in text.split("\n"))
        return text


def preprocess(text: str, source_format: str = "auto") -> str:
    """Convenience-Funktion: Erstellt einen Preprocessor und verarbeitet den Text."""
    preprocessor = TextPreprocessor()
    return preprocessor.preprocess(text, source_format)


if __name__ == "__main__":
    # Schnelltest
    test_text = """# Beispiel-Dokument

Dies ist ein **Test** mit `inline code` und einem Link: [Google](https://google.com).

```python
print("Dieser Code wird entfernt")
```

## Aufzählung

- Punkt eins
- Punkt zwei
- Punkt drei

| Name | Wert |
|------|------|
| Alpha | 42 |
| Beta | 17 |

Die Temperatur beträgt 25°C, d.h. es ist warm.
Der Preis ist >= 100€ bzw. ca. 120€.
"""
    result = preprocess(test_text, source_format="md")
    print("=== Originaltext ===")
    print(test_text)
    print("=== Bereinigter Text ===")
    print(result)
