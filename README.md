# Docmost Markdown Converter

Eine produktionsfähige Anwendung zur Konvertierung von Dokumenten (PDF, DOCX, XLSX) in Docmost-kompatible Markdown-ZIP-Archive.

## Architektur

Das System besteht aus zwei Docker-Services:
1.  **Converter GUI (Port 3000)**: Web-Interface für Uploads, Orchestrierung und Post-Processing.
2.  **Docling Server (Port 5001)**: Backend-Service für die Dokumentenkonvertierung (Kompatibel mit `docling-serve`).

## Voraussetzungen

- Docker & Docker Compose installiert.

## Starten

1.  Repository klonen oder in den Projektordner wechseln.
2.  Starten mit Docker Compose:

    ```bash
    docker-compose up --build
    ```

3.  Die Anwendung ist erreichbar unter: [http://localhost:3000](http://localhost:3000)

## Konfiguration (Optionales externes Docling)

Standardmäßig startet `docker-compose` beide Services. Wenn Sie einen **bereits existierenden Docling-Server** nutzen wollen:

1.  Öffnen Sie `docker-compose.yml`.
2.  Kommentieren Sie den Service `docling-server` aus.
3.  Setzen Sie die Umgebungsvariable `DOCLING_SERVER_URL` für `converter-ui`:
    ```yaml
    environment:
      - DOCLING_SERVER_URL=http://mein-externer-docling-server:5001
    ```
    *(Hinweis: Der externe Server muss die Standard API (`POST /v1/convert/file`) von `docling-serve` bereitstellen.)*

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
