# ReCut

[![Svelte 5](https://img.shields.io/badge/Svelte_5-%23f1413d.svg?style=flat-square&logo=svelte&logoColor=white)](https://svelte.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS_v4-%2338B2AC.svg?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
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

This configuration uses a custom **bridge network** for secure inter-container communication and specifically maps local host directories for both your downloaded clips and internal container data to guarantee persistence.

```yaml
version: "3.8"

services:
  backend:
    image: ghcr.io/g4s01/recut/backend:main
    container_name: recut_backend
    restart: unless-stopped
    ports:
      - "${BACKEND_PORT:-8000}:8000" # Customizable via .env file
    volumes:
      # Map a specific local directory for the extracted clips
      - ./my-clips:/app/downloads
      # Map a specific local directory for internal container data (e.g., yt-dlp cache)
      - ./my-data:/app/data
    environment:
      - HOST=0.0.0.0
      - PORT=8000
    networks:
      - recut_bridge

  frontend:
    image: ghcr.io/g4s01/recut/frontend:main
    container_name: recut_frontend
    restart: unless-stopped
    ports:
      - "${FRONTEND_PORT:-3000}:3000" # Customizable via .env file
    environment:
      # Point the frontend to the backend's external URL (or use default if not set)
      - VITE_API_BASE_URL=${API_BASE_URL:-http://localhost:8000}
    depends_on:
      - backend
    networks:
      - recut_bridge

# Explicitly define a bridge network for the services
networks:
  recut_bridge:
    driver: bridge
```

### Running the application

1. Save the configuration above as `docker-compose.yml` in a directory of your choice.
2. (Optional) Create a `.env` file in the same directory if you need to customize ports or external URLs:

```env
BACKEND_PORT=8000
FRONTEND_PORT=3000
API_BASE_URL=https://api.yourdomain.com
```

3. Run the following command to pull the images and start the containers in the background:

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
