import asyncio
import json
import uuid
import traceback
from typing import List, Optional, Set

from fastapi import BackgroundTasks, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

from storage import save_to_cloud

app = FastAPI(title="Himanshu Automator Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateVideoRequest(BaseModel):
    prompts: List[str]
    json_cookies: Optional[str] = ""
    model: Optional[str] = "seedance-2.0"
    aspect_ratio: Optional[str] = "9:16"
    duration: Optional[int] = 10
    submit_speed: Optional[int] = 1


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
                await ws.send_json(
                    {
                        "type": "log",
                        "message": message,
                    }
                )
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def run_generation(req: GenerateVideoRequest):
    await manager.broadcast("Background task started.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            has_touch=False,
            is_mobile=False,
            java_script_enabled=True,
        )

        if req.json_cookies.strip():
            try:
                cookies = json.loads(req.json_cookies)

                if isinstance(cookies, list):
                    await context.add_cookies(cookies)
                    await manager.broadcast("Cookies loaded successfully.")

            except Exception as e:
                await manager.broadcast(f"Cookie error: {e}")

        else:
            await manager.broadcast("Running without cookies.")

        page = await context.new_page()

        await stealth_async(page)

        try:
            await manager.broadcast("Opening Seedance...")

            await page.goto(
                "https://seedance2.so",
                wait_until="domcontentloaded",
                timeout=60000,
            )

            await manager.broadcast("Website loaded successfully.")

       except Exception as e:
            await manager.broadcast(f"Navigation failed: {e}")

for index, prompt in enumerate(req.prompts, start=1):
            task_id = f"video_{uuid.uuid4().hex[:8]}"
            local_video_path = f"/tmp/{task_id}.mp4"

            await manager.broadcast(
                f"[{index}/{len(req.prompts)}] Processing prompt..."
            )

            try:
                await manager.broadcast("Locating prompt input...")

                await page.fill("textarea", prompt)

                await manager.broadcast("Prompt entered.")

                await manager.broadcast("Clicking Generate...")

                await page.click(
                    "button:has-text('Generate')",
                    timeout=15000,
                )

                await manager.broadcast(
                    "Waiting for video generation..."
                )

                async with page.expect_download(
                    timeout=180000
                ) as download_info:

                    await page.click(
                        "button:has-text('Download')",
                        timeout=120000,
                    )

                download = await download_info.value

                await download.save_as(local_video_path)

                await manager.broadcast(
                    f"Video downloaded: {task_id}.mp4"
                )

                await manager.broadcast(
                    "Uploading to Puter Cloud..."
                )

                await asyncio.to_thread(
                    save_to_cloud,
                    task_id,
                    local_video_path,
                )

                await manager.broadcast(
                    f"Completed: {task_id}"
                )

            except Exception as e:
                error = traceback.format_exc()

                await manager.broadcast(
                    f"Task failed: {e}"
                )

                await manager.broadcast(error)

        await browser.close()

   await manager.broadcast("All tasks completed.")

@app.post("/api/generate-video")
async def generate_video(
    req: GenerateVideoRequest,
    background_tasks: BackgroundTasks,
):
    if not req.prompts:
        return {
            "success": False,
            "message": "No prompts provided.",
        }

    background_tasks.add_task(run_generation, req)

    return {
        "success": True,
        "queued": len(req.prompts),
        "message": "Task queued successfully.",
    }


@app.get("/")
async def root():
    return {
        "name": "Himanshu Automator Backend",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    return {
        "success": True,
        "status": "healthy",
    }
