RAG Project (Azure + Gemini)
Overview

This is a cloud-based RAG (Retrieval-Augmented Generation) system that allows users to upload documents and ask questions from them.

Tech Stack:
FastAPI (backend API),
Streamlit (UI),
Azure Blob Storage (file storage),
Azure Queue (async processing),
Azure AI Search (vector search),
Azure Document Intelligence (PDF extraction) and
Google Gemini (embeddings + LLM)


How it Works:
Upload PDF via UI,
File stored in Azure Blob,
Queue triggers worker,
Worker processes and indexes document,
User asks questions,
Relevant data retrieved + LLM generates answer


Run Locally:
Start API
uvicorn app.api:app
Start Worker
python -m app.worker
Start UI
python -m streamlit run app/ui.py
