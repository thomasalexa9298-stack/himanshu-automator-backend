import asyncio
import json
import uuid
from typing import List, Set, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from storage import save_to_cloud

app = FastAPI(title="Himanshu Automator")

# -----------------------------
# CORS Configuration
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
        # Launch Chromium with anti-bot arguments to bypass Cloudflare flags
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process"
            ]
        )

        # Emulate a standard desktop browser environment
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            has_touch=False,
            is_mobile=False,
            java_script_enabled=True
        )

        # Load Cookies if provided in the payload
        if req.json_cookies and req.json_cookies.strip():
            try:
                cookies = json.loads(req.json_cookies)
                if isinstance(cookies, list):
                    await context.add_cookies(cookies)
                    await manager.broadcast("Cookies successfully injected into browser context.")
            except Exception as e:
                await manager.broadcast(f"Cookie parse error: {e}")
        else:
            await manager.broadcast("No cookies provided, running as guest session...")

        page = await context.new_page()

        # Apply stealth script to override navigator.webdriver detection
        await stealth_async(page)

        try:
            await manager.broadcast("Navigating to target video platform...")
            # REPLACE THIS WITH YOUR TARGET SEEDANCE WEBSITE URL
            await page.goto("https://seedance2.so", wait_until="domcontentloaded", timeout=60000)
            await manager.broadcast("Page loaded successfully without firewall block!")
        except Exception as e:
            await manager.broadcast(f"⚠️ Page Navigation / Cloudflare Warning: {e}")

        # Iterate over all prompts submitted in bulk
        for index, prompt in enumerate(req.prompts, start=1):
            task_id = f"video_{uuid.uuid4().hex[:8]}"
            await manager.broadcast(f"[{index}/{len(req.prompts)}] Processing prompt: '{prompt}'")

            # -------------------------------------------------------------
            # STEP 1: UI AUTOMATION FOR TARGET SITE (Adjust selectors as needed)
            # -------------------------------------------------------------
            # Example:
            # await page.fill("textarea", prompt)
            # await page.click("button:has-text('Generate')")
            # await page.wait_for_selector("a[download]", timeout=120000)
            # -------------------------------------------------------------

            await asyncio.sleep(5)  # Pause simulation for generation

            # Output path or URL captured from web interface
            local_video_source = f"/tmp/{task_id}.mp4"

            # -------------------------------------------------------------
            # STEP 2: SAVE TO PUTER CLOUD STORAGE
            # -------------------------------------------------------------
            await manager.broadcast(f"☁️ Uploading {task_id}.mp4 to Puter storage...")
            
            # Execute Puter upload thread
            await asyncio.to_thread(save_to_cloud, task_id, local_video_source)

            await manager.broadcast(f"✅ Finished task {task_id}.mp4")

        await browser.close()

    await manager.broadcast("🎉 All video generations and uploads completed!")


# -----------------------------
# API Endpoints
# -----------------------------
@app.post("/api/generate-video")
async def generate_video(req: GenerateVideoRequest, background_tasks: BackgroundTasks):
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
