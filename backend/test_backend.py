import asyncio
from main import process_video, ClipRequest

req = ClipRequest(url="https://www.youtube.com/watch?v=jNQXAC9IVRw", start_time=5, end_time=10)
try:
    print(process_video(req))
except Exception as e:
    print("Error:", e)
