# FROM python:3.11-slim
# FROM python:3.13-slim
FROM python:3.14-alpine

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY shared ./shared

CMD ["uvicorn", "backend.app.api:app", "--host", "0.0.0.0", "--port", "8000"]