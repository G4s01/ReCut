# ReCut - Regole dell'Agente (Gemini)

Queste regole definiscono l'architettura, le convenzioni di codice e le direttive per la gestione del progetto "ReCut". Seguile per ogni futuro task di sviluppo.

## 1. Regole Architetturali

Il progetto si basa su un'architettura a container separati tramite Docker Compose:

- **Backend (API)**: Sviluppato in Python con **FastAPI**. Il backend è esclusivamente responsabile dell'esposizione delle API RESTful, dell'interfacciamento con `yt-dlp` e `ffmpeg`, e della gestione del file system locale.
- **Frontend (Web UI)**: Sviluppato in **SvelteKit** con **DaisyUI** e **TailwindCSS**. Il frontend gestisce esclusivamente l'interfaccia utente, la validazione lato client e il consumo delle API REST del backend. Non esegue logiche di business pesanti.
- **Comunicazione**: Il frontend invia richieste HTTP (GET/POST) al backend. I dati viaggiano in formato JSON.

## 2. Convenzioni di Codice

- **Python (FastAPI)**:
  - Usa i **Type Hints** rigorosamente per ogni funzione e modello Pydantic.
  - Implementa percorsi asincroni (`async def`) ove possibile.
  - Utilizza l'integrazione nativa del modulo Python `yt_dlp` al posto di generare subprocessi shell (`subprocess.run`), al fine di mantenere il controllo programmatico asincrono e la gestione degli errori pulita.
  - Rispetta lo standard PEP 8.
- **Svelte / JavaScript**:
  - Scrivi componenti Svelte con blocchi `<script lang="ts">` per godere della tipizzazione di TypeScript.
  - Utilizza le utility class di TailwindCSS e i componenti pre-costruiti di DaisyUI per mantenere lo stile pulito e senza CSS custom, se non strettamente necessario.

## 3. Direttive per la Gestione dei Media Locali

- **Volume Condiviso**: I media scaricati devono risiedere in una directory designata (es. `/app/downloads/` nel container), configurata come Docker Volume per la persistenza tra un riavvio e l'altro (se necessario) ma isolata dal codice sorgente.
- **Garbage Collection**: ReCut _deve_ includere un meccanismo automatico di pulizia. Implementa un task in background (tramite `BackgroundTasks` di FastAPI o simili) per eliminare in automatico i file multimediali scaricati più vecchi di 2-3 ore. Il server non deve diventare uno storage a lungo termine.
- **Isolamento e Sicurezza**: Effettua la sanitizzazione di ogni input dell'utente (URL e filename) per evitare path traversal o l'esecuzione di comandi malevoli, specialmente durante il passthrough verso `yt-dlp`.

## 4. Skill e Competenze Richieste all'Agente

Per operare con successo su questo progetto, applica attivamente le seguenti competenze:

- **Uso di yt-dlp nativo**: Capacità di istanziare `YoutubeDL` con opzioni e hook personalizzati, piuttosto che invocare CLI.
- **Clipping senza Re-encoding**: Competenza approfondita di **FFmpeg** per il taglio dei video. Se l'utente richiede una clip (start/end), l'agente deve sfruttare `--download-sections` (di yt-dlp) oppure eseguire ffmpeg con `-c copy` per tagliare il file senza re-encoding, risparmiando drasticamente cicli CPU.
- **Ottimizzazione Container**: Scrittura di `Dockerfile` multi-stage. Per il backend, usa immagini Python `slim` o `alpine` e installa esplicitamente il binario di `ffmpeg`. Per il frontend, build statica o node server compattato, per mantenere il peso dell'immagine sotto controllo.
