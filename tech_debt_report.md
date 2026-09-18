# Tech Debt Report: ReCut

## 1. Executive Summary

Il progetto sfrutta correttamente lo stack richiesto (SvelteKit + DaisyUI + TailwindCSS per il frontend, FastAPI + yt-dlp per il backend). Tuttavia, il codice attuale mostra segni di stratificazione tipici dello sviluppo iterativo: ci sono utilizzi non idiomatici delle nuove API di Svelte 5 (Runes usate in stile Svelte 4), classi Tailwind kilometriche che scavalcano DaisyUI, e alcune leggerezze nella gestione della concorrenza nel backend.

## 2. Frontend (Svelte 5 / UI)

### 2.1 Svelte 5 Idioms e Anti-Pattern

- **Abuso di `$effect` per side-effects reattivi**: In `+page.svelte`, un blocco `$effect` viene usato per fare il debouncing della `fetch` quando cambia l'`url`. In Svelte 5, l'uso di `$effect` per sincronizzare o triggerare mutazioni di stato/fetch è considerato un anti-pattern. Dovrebbe essere gestito tramite un evento `oninput` sull'input stesso con un debounce esplicito, oppure incapsulando la logica di caricamento.
- **Cascata di stato in `$effect`**: C'è un `$effect` che controlla `formatType` e resetta forzatamente `selectedFormat` se fuori validità. Questo ciclo di reattività nascosta è prono a bug. È preferibile aggiornare `selectedFormat` direttamente nell'event handler (es. `onclick` sui bottoni) che cambia il `formatType`.
- **Mancanza di Snippets**: Il codice del form dei minutaggi ("Start At" e "End At") è completamente duplicato. Svelte 5 ha introdotto la potentissima feature `{#snippet}` che permette di definire frammenti di UI riutilizzabili nello stesso file. Sfruttarla ridurrebbe la verbosità del form del 40%.

### 2.2 DaisyUI vs Tailwind

- **Componenti Nativi Ignorati (Skeleton)**: Il blocco di caricamento della timeline utilizza Tailwind grezzo (`animate-pulse bg-base-200 h-6...`). DaisyUI fornisce nativamente la classe `skeleton` che è più robusta, accessibile e coerente con i temi.
- **Slider CSS-in-Class Ingestibile**: I due `<input type="range">` sovrapposti utilizzano una stringa di classi Tailwind lunga letteralmente decine di righe (`[&::-webkit-slider-thumb]...`). Questo rende il markup illeggibile. Dovrebbe essere astratto in una utility class nel file `app.css` oppure usare le classi native di DaisyUI per i range (`range range-primary`).

## 3. Backend (FastAPI / yt-dlp)

### 3.1 Concorrenza e I/O Bloccante

- **Garbage Collector Bloccante**: La funzione `cleanup_old_files` (lanciata all'avvio) itera i file e li cancella con chiamate sincrone `os.listdir`, `os.stat` e `os.remove`. Sebbene venga eseguita di rado, in un server denso queste operazioni di I/O bloccano l'event loop di `asyncio` in FastAPI. Andrebbero wrapate in `asyncio.to_thread` o scritte usando librerie asincrone come `aiofiles`/`anyio`.

### 3.2 Gestione Errori e Rigidità

- **Errori 500 Invece di 400**: Se nel form si inserisce uno `start_time` superiore all'`end_time`, `process_video` lancia un `ValueError`. Attualmente questo viene catturato da un generico blocco `except Exception as e:` che lancia una `RuntimeError` tradotta poi in un `500 Internal Server Error` da FastAPI, anziché un `400 Bad Request`.
- **Rinominazione File Fragile**: Quando viene richiesto MP3 o WAV, il codice assume ciecamente che `yt-dlp` rinomini il file esattamente come `f"{base}.{req.format}"`. Se `yt-dlp` applica metadata che alterano il nome, l'endpoint fallirà. È preferibile leggere lo standard output di `yt-dlp` o fare un match parziale per garantire la consistenza.

---

## 4. Piano di Sistemazione (Refactoring Plan)

Ecco la checklist step-by-step per sistemare il debito senza rompere l'app:

- [ ] **Step 1: Refactoring Backend (I/O & Eccezioni)**
  - Rendere asincrono l'I/O in `cleanup_old_files` usando `asyncio.to_thread`.
  - Introdurre la cattura di `ValueError` separata da `Exception` generica in `process_video`, ritornando uno stato HTTP 400 per input invalidi.

- [ ] **Step 2: Migrazione Svelte Snippets (Frontend)**
  - Creare un `{#snippet timeInput(type, bindHours, bindMinutes, bindSeconds)}` in `+page.svelte`.
  - Sostituire l'HTML duplicato di "Start At" ed "End At" con lo snippet.

- [ ] **Step 3: Pulizia CSS e DaisyUI (Frontend)**
  - Sostituire il codice grezzo dell'animazione di caricamento con la classe `skeleton` nativa di DaisyUI.
  - Spostare lo spaghetti-CSS dei custom range slider dal markup HTML a una classe definita in un tag `<style>` o in `app.css`.

- [ ] **Step 4: Rimozione `$effect` Anti-Pattern (Frontend)**
  - Eliminare l'`$effect` usato per aggiornare i formati (`selectedFormat`); gestire la logica direttamente nell'`onclick` dei tab di formato.
  - Disaccoppiare la logica di `fetchInfo` (debouncing) dall'`$effect`, spostandola in un vero handler `oninput` sul campo testuale o usando uno store reattivo personalizzato.
