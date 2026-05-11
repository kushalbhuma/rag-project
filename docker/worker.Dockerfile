FROM python:3.14-slim

WORKDIR /app

COPY worker/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY worker ./worker
COPY shared ./shared

CMD ["python", "-u", "-m", "worker.app.worker"]