from fastapi import FastAPI, UploadFile, File
import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient
import json
from fastapi import Form

load_dotenv()

app = FastAPI()

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("AZURE_CONTAINER_NAME")

blob_service_client = BlobServiceClient.from_connection_string(connection_string)

queue_name = os.getenv("AZURE_QUEUE_NAME")

queue_client = QueueClient.from_connection_string(
    conn_str=connection_string,
    queue_name=queue_name
)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...),user_id: str = Form(...)):
    try:
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=f"{user_id}/{file.filename}"   # Organize by user_id in blob storage
        )

        blob_client.upload_blob(file.file, overwrite=True)
        message = {
            "blob_name": f"{user_id}/{file.filename}", 
            "container": container_name,
            "user_id": user_id
        }

        queue_client.send_message(json.dumps(message))

        return {
            "message": "File uploaded & queued for processing",
            "blob_url": blob_client.url
        }

    except Exception as e:
        return {"error": str(e)}