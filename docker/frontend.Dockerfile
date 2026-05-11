FROM python:3.14-alpine

WORKDIR /app

COPY frontend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY frontend ./frontend
COPY shared ./shared

CMD ["streamlit", "run", "frontend/app/ui.py", "--server.port=8501", "--server.address=0.0.0.0"]