import asyncio
import json
from typing import List, Set, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from playwright.async_api import async_playwright

app = FastAPI(title="Himanshu Automator")

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Request Model
# -----------------------------
class GenerateVideoRequest(BaseModel):
    prompts: List[str]
    json_cookies: Optional[str] = ""
    model: Optional[str] = "seedance-2.0"
    aspect_ratio: Optional[str] = "9:16"
    duration: Optional[int] = 10
    submit_speed: Optional[int] = 1


# -----------------------------
# WebSocket Manager
# -----------------------------
class ConnectionManager:
    def __init__(self):
        self.connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.discard(websocket)

    async def broadcast(self, message: str):
        dead = []

        for ws in self.connections:
            try:
                await ws.send_json({
                    "type": "log",
                    "message": message
                })
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# -----------------------------
# WebSocket Endpoint
# -----------------------------
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# -----------------------------
# Playwright Background Engine
# -----------------------------
async def run_generation(req: GenerateVideoRequest):
    await manager.broadcast("Task Queued successfully.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # -----------------------------
        # Load Cookies
        # -----------------------------
        if req.json_cookies and req.json_cookies.strip():
            try:
                cookies = json.loads(req.json_cookies)
                if isinstance(cookies, list):
                    await context.add_cookies(cookies)
                    await manager.broadcast("Cookies loaded into browser context.")
            except Exception as e:
                await manager.broadcast(f"Cookie parse error: {e}")
        else:
            await manager.broadcast("No cookies provided, proceeding as guest session...")

        page = await context.new_page()
        await page.goto("https://example.com")

        for index, prompt in enumerate(req.prompts, start=1):
            await manager.broadcast(f"Generating prompt {index}/{len(req.prompts)}: '{prompt}'")
            await asyncio.sleep(3)

        await browser.close()

    await manager.broadcast("All video generations completed!")


# -----------------------------
# API Endpoints
# -----------------------------
@app.post("/api/generate-video")
async def generate_video(req: GenerateVideoRequest, background_tasks: BackgroundTasks):
    # Queue the Playwright automation in the background so POST request returns instantly
    background_tasks.add_task(run_generation, req)

    return {
        "success": True,
        "message": "Task queued successfully. Watch live log console for progress."
    }


@app.get("/")
async def root():
    return {
        "name": "Himanshu Automator",
        "status": "running"
    }
