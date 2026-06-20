# Repository-Konventionen

## Umsetzungspläne

Alle Umsetzungs- und Implementierungspläne werden im Ordner `operations/` abgelegt.

### Struktur

```
operations/
├── <projektname>/
│   ├── implementation_plan.md    # Umsetzungsplan
│   └── ...                       # Weitere Dokumente
└── ...
```

### Regeln für KI-Assistenten

> **WICHTIG**: Wenn du einen neuen Umsetzungsplan erstellst, speichere ihn IMMER
> unter `operations/<projektname>/implementation_plan.md` im Repository.
> Erstelle einen neuen Unterordner pro Projekt/Feature.

## Projektstruktur

- Jedes Lernprojekt hat seinen eigenen Ordner im Repository-Root
- Umsetzungspläne werden separat in `operations/` gehalten
- Sensible Daten (API-Keys etc.) gehören in `.env`-Dateien und werden NICHT committed
