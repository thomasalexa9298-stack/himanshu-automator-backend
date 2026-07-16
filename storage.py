import os
import urllib.request
import boto3

def save_to_cloud(task_id: str, video_url: str):
    local_path = f"/tmp/{task_id}.mp4"
    
    # 1. Download temp file
    urllib.request.urlretrieve(video_url, local_path)
    
    # 2. Upload to S3 / Cloudflare R2
    s3_client = boto3.client(
        's3',
        endpoint_url=os.getenv("S3_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    
    bucket_name = os.getenv("S3_BUCKET_NAME", "seedance-videos")
    s3_client.upload_file(local_path, bucket_name, f"{task_id}.mp4")
    
    # 3. Clean up local temp file
    if os.path.exists(local_path):
        os.remove(local_path)
        
    print(f"📦 Successfully stored {task_id}.mp4 in {bucket_name}")
