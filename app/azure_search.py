from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery
from google import genai

from app.config import (
    GOOGLE_API_KEY,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_INDEX,
    AZURE_SEARCH_KEY
)

# Gemini client (for embedding)
client = genai.Client(api_key=GOOGLE_API_KEY)

# Azure Search client
search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=AZURE_SEARCH_INDEX,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY)
)

def retrieve_chunks(query, source=None, user_id=None):
    print("[Retriever Source]:", source)

    # Convert query into embedding
    response = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=query
    )

    embedding = response.embeddings[0].values

    # Vector search
    vector_query = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=3,
        fields="embedding"
    )

    # Add filter for source and user_id if provided
    if source and user_id:
        results = search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=f"source eq '{source}' and user_id eq '{user_id}'", # ensure source is indexed as a field in Azure Search
            top=3
        )
    elif user_id:
        results = search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=f"user_id eq '{user_id}'"
        )

    print("DEBUG SOURCE:", repr(source))
    print("DEBUG USER_ID:", repr(user_id))

    # Collect chunks
    chunks = []
    for result in results:
        print(result)
        chunks.append(result["content"])

    return "\n\n".join(chunks)