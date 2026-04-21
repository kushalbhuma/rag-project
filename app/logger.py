import json
import uuid
import logging
from datetime import datetime

from azure.monitor.opentelemetry import configure_azure_monitor
from app.config import AZURE_MONITOR_CONNECTION_STRING

if not AZURE_MONITOR_CONNECTION_STRING:
    raise ValueError("Azure Monitor connection string not found")

# Configure Azure Monitor (OpenTelemetry)
configure_azure_monitor(connection_string=AZURE_MONITOR_CONNECTION_STRING)

# Create logger
logger = logging.getLogger("rag_logger")
logger.setLevel(logging.INFO)


def generate_session_id():
    return str(uuid.uuid4())


def generate_question_id():
    return str(uuid.uuid4())


def log_interaction(data):
    log = {
        "session_id": data.get("session_id"),
        "question_id": data.get("question_id"),
        "query": data.get("query"),
        "response": data.get("response"),
        "hallucination": data.get("hallucination"),
        "toxicity": data.get("toxicity"),
        "prompt_injection": data.get("prompt_injection"),
        "timestamp": datetime.utcnow().isoformat()
    }

    logger.info(json.dumps(log))

    # local print for debugging
    print("\n[LOG]:", json.dumps(log, indent=2))