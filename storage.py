import os
import requests

def save_to_cloud(task_id: str, file_source: str):
    """
    Uploads generated videos directly to Puter Cloud Storage.
    `file_source` is either a local file path from Playwright or a web URL.
    """
    token = os.getenv("PUTER_AUTH_TOKEN")
    if not token:
        print("❌ Error: PUTER_AUTH_TOKEN is missing in environment variables!")
        return

    file_name = f"{task_id}.mp4"
    local_path = f"/tmp/{file_name}"

    # 1. Prepare local video file
    if file_source.startswith("http://") or file_source.startswith("https://"):
        print(f"📥 Downloading temporary file from {file_source}...")
        res = requests.get(file_source, stream=True)
        with open(local_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    else:
        local_path = file_source

    # 2. Upload file to Puter Cloud Storage via API
    url = f"https://api.puter.com/drivers/express/fs/write?path={file_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "video/mp4"
    }

    print(f"☁️ Uploading {file_name} to Puter Cloud...")
    
    with open(local_path, "rb") as video_file:
        response = requests.post(url, headers=headers, data=video_file)

    if response.status_code in [200, 201]:
        print(f"📦 Successfully stored {file_name} on Puter!")
    else:
        print(f"❌ Puter Upload Failed ({response.status_code}): {response.text}")

    # 3. Clean up temp local file
    if os.path.exists(local_path) and local_path.startswith("/tmp/"):
        os.remove(local_path)
