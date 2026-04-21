import os
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from google import genai
import numpy as np
from pypdf import PdfReader, PdfWriter

import re
from io import BytesIO

from app.config import (
    DOCINTEL_ENDPOINT,
    DOCINTEL_KEY,
    GOOGLE_API_KEY,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_INDEX,
    AZURE_SEARCH_KEY
)
# Azure Document Intelligence setup
docintel_client = DocumentIntelligenceClient(
    endpoint=DOCINTEL_ENDPOINT,
    credential=AzureKeyCredential(DOCINTEL_KEY)
)


# Gemini setup
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)

def process_and_index(pdf_bytes, file_name, user_id):
    
    reader = PdfReader(BytesIO(pdf_bytes))
    total_pages = len(reader.pages)

    print("Total pages:", total_pages)

    full_text = ""

    for start in range(0, total_pages, 2):

        writer = PdfWriter()

        for page_num in range(start, min(start + 2, total_pages)):
            writer.add_page(reader.pages[page_num])

        temp_file = f"temp_{start}.pdf"

        with open(temp_file, "wb") as f:
            writer.write(f)

        with open(temp_file, "rb") as f:
            poller = docintel_client.begin_analyze_document(
                "prebuilt-layout",
                body=f
            )

        result = poller.result()

        for page in result.pages:
            for line in page.lines:
                full_text += line.content + "\n"

        os.remove(temp_file)

    print("\nText extracted successfully")


    # Split text into chunks
    chunk_size = 500
    overlap = 100

    chunks = []

    for i in range(0, len(full_text), chunk_size - overlap):
        chunk = full_text[i:i + chunk_size].strip()
        if chunk:
            chunks.append(chunk)

    print("Total chunks:", len(chunks))


    # Generate embeddings
    embeddings = []

    for chunk in chunks:
        response = gemini_client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=chunk
        )
        embeddings.append(response.embeddings[0].values)

    embedding_matrix = np.array(embeddings).astype("float32")


    #  Store in Azure Search
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX,
        credential=AzureKeyCredential(AZURE_SEARCH_KEY)
    )

    documents = []

    # remove folder (user_id/) first
    file_only = file_name.split("/")[-1]

    raw_name = file_only.rsplit(".", 1)[0]

    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', raw_name)

    safe_name = f"{user_id}_{clean_name}"

    

    for i, chunk in enumerate(chunks):
        documents.append({
            "id": f"{safe_name}_{i}",
            "content": chunk,
            "embedding": embedding_matrix[i].tolist(),
            "source": safe_name,
            "user_id": user_id
        })
    

    print("\nUploading to Azure AI Search...")

    result = search_client.upload_documents(documents)

    print("Upload result:", result)
    

   