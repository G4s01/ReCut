# ReCut

[![Svelte 5](https://img.shields.io/badge/Svelte_5-%23f1413d.svg?style=flat-square&logo=svelte&logoColor=white)](https://svelte.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS_v4-%2338B2AC.svg?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![daisyUI](https://img.shields.io/badge/daisyUI-5A0EF8?style=flat-square&logo=daisyui&logoColor=white)](https://daisyui.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

> A modern web app to extract clips from videos instantly and without re-encoding.

ReCut provides a lightning-fast way to trim, crop, and download video segments. By combining a powerful Python backend (`yt-dlp` and `ffmpeg -c copy` for zero re-encoding) with a snappy Svelte 5 and DaisyUI frontend, it brings a seamless clipping experience right to your browser.

## Features

- **Instant Clipping**: Extract video sections instantly without re-encoding, preserving original quality.
- **Broad Platform Support**: Leverages `yt-dlp` to fetch media metadata and content from hundreds of supported platforms.
- **Modern UI**: Clean, responsive, and beautiful interface built with Svelte 5, Tailwind CSS v4, and DaisyUI.
- **Automatic Garbage Collection**: Background tasks automatically clean up old media files to prevent storage bloat.
- **Containerized**: Designed for Docker Compose, isolating services for security, simplicity, and ease of deployment.

## Architecture

ReCut is composed of two loosely coupled services:

1. **Frontend (Web UI)**: A SvelteKit application handling the user interface and API consumption.
2. **Backend (API)**: A Python FastAPI service handling the heavy lifting—extracting info natively with `yt-dlp` and slicing videos with `ffmpeg`.

## Getting Started

The recommended way to deploy ReCut is via Docker Compose. Below is a complete, well-commented configuration that sets up both the frontend and backend.

This configuration maps local host directories for both your downloaded clips and internal container data to guarantee persistence. The backend uses host networking to bypass DNS restrictions often found on routers (like OpenWRT/Alpine).

```yaml
services:
  backend:
    image: ghcr.io/g4s01/recut/backend:latest
    container_name: recut_backend
    restart: unless-stopped
    # FIX for OpenWRT / Alpine DNS issues: Uses the host's native networking and DNS
    network_mode: "host"
    # Port mapping is ignored in host mode. Backend will run on port 8000.
    volumes:
      # Map a specific local directory for the extracted clips
      - ./my-clips:/app/downloads
      # Map a specific local directory for internal container data (e.g., yt-dlp cache)
      - ./backend-data:/app/data
    environment:
      - HOST=0.0.0.0
      - PORT=8000

  frontend:
    image: ghcr.io/g4s01/recut/frontend:latest
    container_name: recut_frontend
    restart: unless-stopped
    ports:
      - "3000:3000" # Format is HOST:CONTAINER. Change the first port (left side) to expose on a different host port
    environment:
      # Point the frontend to the backend's external URL (or use default if not set)
      - PUBLIC_API_URL=${API_BASE_URL:-http://localhost:8000}
```

### Running the application

1. Save the configuration above as `docker-compose.yml` in a directory of your choice.
2. Run the following command to pull the images and start the containers in the background:

```bash
docker compose up -d
```

Once started:

- Access the **Web UI** at `http://localhost:3000` (or your custom port/domain).
- Access the **API Documentation** (Swagger UI) at `http://localhost:8000/docs`.

> [!NOTE]
> All processed clips will be safely stored in the `./my-clips` directory on your host machine. The backend's built-in garbage collector automatically removes media older than 2-3 hours to prevent storage bloat.

## Local Development

If you prefer to run the components directly on your host machine for development:

### Backend

Requires Python 3.10+, `ffmpeg`, and `yt-dlp` available in your system `PATH`.

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

Requires Node.js 18+.

```bash
cd frontend
npm install
npm run dev
```
