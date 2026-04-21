# This code defines a FastAPI application that allows users to upload files, which are then stored in Azure Blob Storage and a message is sent to an Azure Queue for further processing. The application uses environment variables to configure the connection to Azure services.
from fastapi import FastAPI, UploadFile, File

from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient
import json
from fastapi import Form
from app.config import (
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_CONTAINER_NAME,
    AZURE_QUEUE_NAME,
    validate_config
)
validate_config()

app = FastAPI()

blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

queue_client = QueueClient.from_connection_string(
    conn_str=AZURE_STORAGE_CONNECTION_STRING,
    queue_name=AZURE_QUEUE_NAME
)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...),user_id: str = Form(...)):
    try:
        blob_client = blob_service_client.get_blob_client(
            container=AZURE_CONTAINER_NAME,
            blob=f"{user_id}/{file.filename}"   # Organize by user_id in blob storage
        )

        blob_client.upload_blob(file.file, overwrite=True)
        message = {
            "blob_name": f"{user_id}/{file.filename}", 
            "container": AZURE_CONTAINER_NAME,
            "user_id": user_id
        }

        queue_client.send_message(json.dumps(message))

        return {
            "message": "File uploaded & queued for processing",
            "blob_url": blob_client.url
        }

    except Exception as e:
        return {"error": str(e)}