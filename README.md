# Conrad Kategorisierer

**Professionelle Desktop-Anwendung zur automatischen Kategorie-Zuordnung für Conrad.de Produktlisten.**

---

## Funktionsumfang

| Funktion | Beschreibung |
|---|---|
| **Excel-Import** | Öffnet `.xlsx`-Produktchecklisten per Drag-and-Drop oder Dateiauswahl |
| **Online-Suche** | Durchsucht Conrad.de nach EAN, Hersteller-Referenz und Produktname |
| **Keyword-Fallback** | Über 20 vordefinierte Regeln für häufige Produktkategorien |
| **Lokaler Cache** | Bereits aufgelöste Kategorien werden zwischengespeichert |
| **Parent-Zuordnung** | Schreibt die 7-stellige Kategorie-ID (mit führenden Nullen) in die Parent-Spalte |
| **„Manuell pflegen"** | Produkte ohne eindeutige Zuordnung werden klar markiert |
| **Inkrementelles Speichern** | Alle 5 Zeilen wird die Ausgabedatei gespeichert |
| **Originales Formatting** | Bestehende Excel-Formatierung bleibt vollständig erhalten |
| **Live-Ergebnistabelle** | Verarbeitete Produkte werden in Echtzeit angezeigt |
| **Helles / Dunkles Design** | Vollständig umschaltbares Interface |

---

## Installation

### Voraussetzungen

- Python 3.11 oder neuer
- pip

### Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### Anwendung starten

```bash
python conrad_app.py
```

---

## Verteilung (Standalone)

Fertige Binaries werden automatisch über GitHub Actions erstellt:

| Plattform | Artifact |
|---|---|
| **Windows 10 / 11** | `ConradKategorisierer.exe` (Einzeldatei) |
| **macOS Apple Silicon** | `ConradKategorisierer-AppleSilicon.zip` |
| **macOS Intel** | `ConradKategorisierer-Intel.zip` |

Die Builds werden bei jedem Push auf `main` oder `master` ausgeführt und stehen als GitHub Actions Artifacts zum Download bereit.

---

## Projektstruktur

```
Conrad-Categoriser/
├── conrad_app.py              # Einstiegspunkt
├── requirements.txt
├── assets/
│   └── conrad_logo.png
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # Hauptfenster (PySide6)
│   └── theme.py               # Design-System (Farben, Stylesheets)
├── categorizer/
│   ├── __init__.py
│   ├── lookup.py              # Conrad.de-Suche, Keyword-Matching
│   └── excel_processor.py     # openpyxl Lese- / Schreiblogik
└── .github/
    └── workflows/
        └── build.yml          # CI/CD Build-Pipeline
```

---

## Bedienung

1. Anwendung starten
2. Excel-Datei per Drag-and-Drop in das Fenster ziehen **oder** auf den Upload-Bereich klicken
3. Auf **„Verarbeitung starten"** klicken
4. Fortschritt und Ergebnisse werden live angezeigt
5. Nach Abschluss: **„Ergebnis öffnen"** oder **„Ordner öffnen"** verwenden

---

## Lizenz

Internes Werkzeug – Conrad Electronic SE.
