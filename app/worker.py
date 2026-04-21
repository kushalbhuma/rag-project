# change from feature branch ONLY (rebase demo)
import os
import json
import time
from dotenv import load_dotenv

from azure.storage.queue import QueueClient
from azure.storage.blob import BlobServiceClient

from index_pipeline import process_and_index   

# Load env
load_dotenv()

# Azure setup
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
queue_name = os.getenv("AZURE_QUEUE_NAME")

# Queue client
queue_client = QueueClient.from_connection_string(
    conn_str=connection_string,
    queue_name=queue_name
)

# Blob client
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

print("🚀 Worker started... Listening to queue...")

# Loop
while True:
    try:
        messages = queue_client.receive_messages(
            messages_per_page=1,
            visibility_timeout=60
        )

        for message_batch in messages.by_page():
            for msg in message_batch:

                print("\n📩 New message received")

                data = json.loads(msg.content)

                blob_name = data["blob_name"]
                container_name = data["container"]
                user_id = data["user_id"]

                print(f"📄 File: {blob_name}")

                # Download file
                blob_client = blob_service_client.get_blob_client(
                    container=container_name,
                    blob=blob_name
                )

                pdf_bytes = blob_client.download_blob().readall()

                print("⬇️ Downloaded from Blob")

                try:
                    # pass file name
                    process_and_index(pdf_bytes, blob_name, user_id)

                    queue_client.delete_message(msg)
                    print("✅ Indexed & message removed")

                except Exception as e:
                    print(" Processing failed:", str(e))
                    queue_client.delete_message(msg)

        time.sleep(5)

    except Exception as e:
        print(" Worker error:", str(e))
        time.sleep(5)