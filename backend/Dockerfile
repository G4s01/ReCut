# Usa una base slim in ottemperanza alle regole
FROM python:3.11-slim

# Installa ffmpeg, strettamente necessario per le manipolazioni video
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# (Placeholder) Copia il file delle dipendenze e installale
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice sorgente
COPY . .

# Esponi la porta 8000 per FastAPI
EXPOSE 8000

# Avvia l'applicazione FastAPI usando uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
