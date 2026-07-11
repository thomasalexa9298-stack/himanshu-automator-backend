import asyncio
import json
from typing import List, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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
    json_cookies: str
    model: str = "seedance-2.0"
    aspect_ratio: str = "9:16"
    duration: int = 15


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
# WebSocket
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
# Playwright Demo
# -----------------------------
async def run_generation(req: GenerateVideoRequest):

    await manager.broadcast("Queued")

    generated_urls = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        context = await browser.new_context()

        # -----------------------------
        # Load Cookies
        # -----------------------------
        try:
            cookies = json.loads(req.json_cookies)

            if isinstance(cookies, list):
                await context.add_cookies(cookies)
                await manager.broadcast("Cookies loaded")

        except Exception as e:
            await manager.broadcast(f"Cookie parse error: {e}")

        page = await context.new_page()

        #
        # Replace this URL with your own application or an official,
        # authorized endpoint/API for your workflow.
        #
        await page.goto("https://example.com")

        for index, prompt in enumerate(req.prompts, start=1):

            await manager.broadcast(
                f"Generating {index}/{len(req.prompts)}"
            )

            #
            # ------------------------------------------------------
            # YOUR AUTHORIZED PLAYWRIGHT AUTOMATION GOES HERE
            #
            # Example:
            #   await page.fill(...)
            #   await page.click(...)
            #   await page.wait_for_selector(...)
            #
            # If using an official API instead of browser automation,
            # replace this section with API calls.
            # ------------------------------------------------------
            #

            await asyncio.sleep(3)

            generated_urls.append(
                f"https://example.com/generated/video_{index}.mp4"
            )

        await browser.close()

    await manager.broadcast("Completed")

    return generated_urls


# -----------------------------
# API
# -----------------------------
@app.post("/api/generate-video")
async def generate_video(req: GenerateVideoRequest):

    urls = await run_generation(req)

    return {
        "success": True,
        "count": len(urls),
        "videos": urls
    }


@app.get("/")
async def root():
    return {
        "name": "Himanshu Automator",
        "status": "running"
    }
