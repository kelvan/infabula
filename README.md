# infabula 🍼

Einfaches Babytagebuch als lokale Webanwendung.

## Setup

```bash
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

Dann im Browser: http://localhost:8080  
Von anderen Geräten im LAN: http://<server-ip>:8080

## Funktionen

- **Windel** – Zeitpunkt + Art (nass/schmutzig/beides)
- **Stillen** – Beginn/Ende + Seite
- **Fläschchen** – Zeitpunkt + Menge (ml) + Inhalt
- **Schlaf** – Einschlafen/Aufwachen → automatische Dauer
- **Gewicht** – Zeitpunkt + Gramm
- **Notiz** – Freitext

## Auswertung

- Letztes Ereignis pro Typ + "vor X Minuten"
- Abstände zwischen Windeln / Stillen / Fläschchen (letzter + Durchschnitt)
- Schlafdauer-Balkendiagramm (letzte 10 Schläfe)
- IP-Farben: jedes Gerät im Netz bekommt automatisch eine eigene Farbe

## Daten

SQLite-Datenbank `infabula.db` im gleichen Verzeichnis – kein Cloud, alles lokal.

## Podman/Docker (optional)

```bash
podman build -t infabula .
podman run -p 8080:8080 -v ./data:/app/data infabula
```

Dann DB-Pfad in main.py auf `/app/data/infabula.db` ändern.
