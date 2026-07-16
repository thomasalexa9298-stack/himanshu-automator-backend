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
        # Iterate over all prompts submitted in bulk
        for index, prompt in enumerate(req.prompts, start=1):
            task_id = f"video_{uuid.uuid4().hex[:8]}"
            await manager.broadcast(f"[{index}/{len(req.prompts)}] Processing prompt: '{prompt}'")

            local_video_source = f"/tmp/{task_id}.mp4"

            try:
                # 1. Prompt box dhoondho aur text fill karo
                await page.fill("textarea", prompt)
                await manager.broadcast("Prompt entered into box.")

                # 2. Generate button click karo
                await page.click("button:has-text('Generate')")
                await manager.broadcast("Click 'Generate'. Waiting for video render...")

                # 3. Video ready hone tak wait karo aur download event capture karo
                async with page.expect_download(timeout=180000) as download_info:
                    # Agar target site par direct Download button hai:
                    await page.click("button:has-text('Download')", timeout=120000)

                download = await download_info.value
                await download.save_as(local_video_source)
                await manager.broadcast(f"Video saved locally to {local_video_source}")

                # 4. Puter Cloud Storage me Upload karo
                aimport asyncio
import json
import uuid
import traceback
from typing import List, Set, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from storage import save_to_cloud

app = FastAPI(title="Himanshu Automator Backend")

# -------------------------------------------------------------
# CORS Configuration (Allows requests from any frontend origin)
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# Request Schema Model
# -------------------------------------------------------------
class GenerateVideoRequest(BaseModel):
    prompts: List[str]
    json_cookies: Optional[str] = ""
    model: Optional[str] = "seedance-2.0"
    aspect_ratio: Optional[str] = "9:16"
    duration: Optional[int] = 10
    submit_speed: Optional[int] = 1


# -------------------------------------------------------------
# Live WebSocket Connection Manager for Console Telemetry
# -------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.discard(websocket)

    async def broadcast(self, message: str):
        """Sends real-time logs to all connected WebSocket clients."""
        dead_sockets = []
        for ws in self.connections:
            try:
                await ws.send_json({
                    "type": "log",
                    "message": message
                })
            except Exception:
                dead_sockets.append(ws)

        for ws in dead_sockets:
            self.disconnect(ws)


manager = ConnectionManager()


# -------------------------------------------------------------
# WebSocket Endpoint for Live Client Log Console
# -------------------------------------------------------------
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keeps connection alive while receiving heartbeat messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# -------------------------------------------------------------
# Playwright Background Engine Task
# -------------------------------------------------------------
async def run_generation(req: GenerateVideoRequest):
    await manager.broadcast("🚀 [INIT] Background task picked up by Railway worker.")

    async with async_playwright() as p:
        # Launch headless Chromium with stealth anti-bot flags
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security"
            ]
        )

        # Build realistic browser user context
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )

        # Inject session cookies if provided in POST request payload
        if req.json_cookies and req.json_cookies.strip():
            try:
                cookies = json.loads(req.json_cookies)
                if isinstance(cookies, list):
                    await context.add_cookies(cookies)
                    await manager.broadcast("🍪 Cookies successfully loaded into browser context.")
            except Exception as e:
                await manager.broadcast(f"⚠️ Cookie Injection Error: {str(e)}")
        else:
            await manager.broadcast("ℹ️ No cookies passed, proceeding in guest mode...")

        page = await context.new_page()
        await stealth_async(page)

        try:
            target_url = "https://seedance2.so"  # Change this to your target website URL
            await manager.broadcast(f"🌐 Navigating to {target_url}...")
            await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            await manager.broadcast("✅ Target webpage loaded successfully!")
        except Exception as e:
            await manager.broadcast(f"❌ Firewall/Navigation Error: {str(e)}")

        # Execute automation for each prompt sequentially
        for index, prompt in enumerate(req.prompts, start=1):
            task_id = f"video_{uuid.uuid4().hex[:8]}"
            local_video_path = f"/tmp/{task_id}.mp4"

            await manager.broadcast(f"\n🎬 [{index}/{len(req.prompts)}] Starting task '{task_id}'")
            await manager.broadcast(f"📝 Prompt: '{prompt}'")

            try:
                # --- STEP 1: Enter Prompt ---
                await manager.broadcast("🔍 Locating prompt text input box...")
                # Update selector 'textarea' if your site uses input[type='text']
                await page.fill("textarea", prompt)
                await manager.broadcast("✏️ Prompt text entered.")

                # --- STEP 2: Click Generate Button ---
                await manager.broadcast("👆 Looking for Generate button...")
                # Searches for buttons matching 'Generate', 'Create', or 'Run'
                await page.click("button:has-text('Generate'), button:has-text('Create')", timeout=15000)
                await manager.broadcast("⏳ Clicked Generate! Waiting for video generation process...")

                # --- STEP 3: Wait & Capture Download ---
                await manager.broadcast("⌛ Waiting for download link/button to trigger...")
                
                # Listen for browser download event
                async with page.expect_download(timeout=180000) as download_info:
                    await page.click("button:has-text('Download'), a[download]", timeout=120000)

                download = await download_info.value
                await download.save_as(local_video_path)
                await manager.broadcast(f"💾 Video downloaded locally to {local_video_path}")

                # --- STEP 4: Store in Puter Cloud ---
                await manager.broadcast(f"☁️ Transferring {task_id}.mp4 to Puter Cloud Storage...")
                await asyncio.to_thread(save_to_cloud, task_id, local_video_path)
                await manager.broadcast(f"🎉 Task {task_id} completed successfully!")

            except Exception as err:
                error_details = traceback.format_exc()
                await manager.broadcast(f"❌ Error processing Prompt #{index}: {str(err)}")
                await manager.broadcast(f"🐛 Debug Trace: {error_details[:200]}...")

        await browser.close()

    await manager.broadcast("\n🏁 All bulk video tasks finished!")


# -------------------------------------------------------------
# REST API Trigger Endpoint
# -------------------------------------------------------------
@app.post("/api/generate-video")
async def generate_video(req: GenerateVideoRequest, background_tasks: BackgroundTasks):
    # Enqueue background task
    background_tasks.add_task(run_generation, req)
    return {
        "success": True,
        "message": "Task queued successfully. Watch live log console for progress."
    }


# -------------------------------------------------------------
# Server Health Check Route
# -------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "name": "Himanshu Automator Engine",
        "status": "running"
    }wait manager.broadcast(f"☁️ Uploading {task_id}.mp4 to Puter storage...")
                await asyncio.to_thread(save_to_cloud, task_id, local_video_source)
                await manager.broadcast(f"✅ Finished task {task_id}.mp4")

            except Exception as err:
                await manager.broadcast(f"❌ Error during generation for prompt {index}: {err}")


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
