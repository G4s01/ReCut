import asyncio
import os
import time
from typing import Annotated
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
import yt_dlp

DOWNLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "downloads"))
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

async def cleanup_old_files():
    """Background task to delete files older than 2 hours."""
    while True:
        try:
            now = time.time()
            for filename in os.listdir(DOWNLOADS_DIR):
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                if os.path.isfile(filepath):
                    # 7200 seconds = 2 hours
                    if os.stat(filepath).st_mtime < now - 7200:
                        os.remove(filepath)
        except Exception as e:
            print(f"Cleanup error: {e}")
        await asyncio.sleep(3600)  # Run every hour

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(cleanup_old_files())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/downloads", StaticFiles(directory=DOWNLOADS_DIR), name="downloads")

class ClipRequest(BaseModel):
    url: HttpUrl
    start_time: int | float | None = None
    end_time: int | float | None = None
    media_format: str = "video"
    format: str = "mp4"

class ClipResponse(BaseModel):
    file_url: str
    filename: str

class InfoRequest(BaseModel):
    url: HttpUrl

class InfoResponse(BaseModel):
    duration: float | None = None
    title: str | None = None

@app.post("/api/info")
async def get_info(req: InfoRequest) -> InfoResponse:
    url_str = str(req.url)
    if not url_str.startswith("http://") and not url_str.startswith("https://"):
        raise ValueError("Invalid URL scheme")
        
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'source_address': '0.0.0.0',
        'force_ipv4': True,
        'nocheckcertificate': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = await asyncio.to_thread(ydl.extract_info, url_str, download=False)
            return InfoResponse(
                duration=info.get('duration'),
                title=info.get('title')
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=str(e))

def process_video(req: ClipRequest) -> str:
    if req.start_time is not None and req.end_time is not None:
        if req.start_time >= req.end_time:
            raise ValueError("start_time must be less than end_time")
            
    # Sanitize URL by ensuring it's an http/https string
    url_str = str(req.url)
    if not url_str.startswith("http://") and not url_str.startswith("https://"):
        raise ValueError("Invalid URL scheme")

    opts = {
        'outtmpl': os.path.join(DOWNLOADS_DIR, '%(id)s_%(epoch)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'source_address': '0.0.0.0',
        'force_ipv4': True,
        'nocheckcertificate': True,
    }
    
    if req.format in ['mp3', 'wav']:
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': req.format,
            'preferredquality': '192',
        }]
    elif req.format == 'm4a':
        opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
    elif req.format == 'opus':
        opts['format'] = 'bestaudio[ext=opus]/bestaudio/best'
    elif req.format == 'webm':
        if req.media_format == 'video_only':
            opts['format'] = 'bestvideo[ext=webm]/bestvideo/best'
        else:
            opts['format'] = 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best'
    else:
        if req.media_format == 'video_only':
            opts['format'] = 'bestvideo[ext=mp4]/bestvideo/best'
        else:
            opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    
    if req.start_time is not None or req.end_time is not None:
        start = req.start_time if req.start_time is not None else 0
        end = req.end_time if req.end_time is not None else float('inf')
        opts['download_ranges'] = lambda info, ydl: [{'start_time': start, 'end_time': end}]

    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url_str, download=True)
            if 'requested_downloads' in info and info['requested_downloads']:
                filepath = info['requested_downloads'][0]['filepath']
            else:
                filepath = ydl.prepare_filename(info)
                
            if req.format in ['mp3', 'wav']:
                base, _ = os.path.splitext(filepath)
                filepath = f"{base}.{req.format}"
                
            return os.path.basename(filepath)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise RuntimeError(str(e))

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(DOWNLOADS_DIR, safe_filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    from fastapi.responses import FileResponse
    return FileResponse(
        path=filepath, 
        filename=safe_filename, 
        media_type="application/octet-stream"
    )

@app.post("/api/clip")
async def create_clip(req: ClipRequest) -> ClipResponse:
    try:
        filename = await asyncio.to_thread(process_video, req)
        return ClipResponse(
            file_url=f"/api/download/{filename}",
            filename=filename
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
