# Docmost Markdown Converter

Eine produktionsfähige Anwendung zur Konvertierung von Dokumenten (PDF, DOCX, XLSX) in Docmost-kompatible Markdown-ZIP-Archive.

## Architektur

Das System besteht aus einem Docker-Service:
1.  **Converter GUI (Port 3000)**: Web-Interface, das Anfragen an einen externen `docling-serve` weiterleitet.

## Voraussetzungen

- Docker & Docker Compose installiert.

## Starten

1.  Repository klonen oder in den Projektordner wechseln.
2.  Starten mit Docker Compose:

    ```bash
    docker-compose up --build
    ```

3.  Die Anwendung ist erreichbar unter: [http://localhost:3000](http://localhost:3000)

## Konfiguration

Setzen Sie die Umgebungsvariable `DOCLING_SERVER_URL` in der `docker-compose.yml` auf Ihren Docling-Server:

```yaml
environment:
    - DOCLING_SERVER_URL=http://mein-server:5001
```

*(Hinweis: Der Server muss die Standard API (`POST /v1/convert/file`) von `docling-serve` bereitstellen.)*

## Nutzung

1.  Öffnen Sie `http://localhost:3000`.
2.  Laden Sie eine PDF, DOCX oder XLSX Datei hoch.
3.  Klicken Sie auf "Convert & Download".
4.  Nach kurzer Zeit wird ein `_docmost.zip` heruntergeladen.

### Output Format

Das ZIP-Archiv enthält:
- `document.md`: Das bereinigte Markdown.
- `images/`: Ordner mit extrahierten Bildern (`image_001.png`, etc.).

Das Markdown ist optimiert für den Import in Docmost (kein HTML, bereinigte Struktur).
