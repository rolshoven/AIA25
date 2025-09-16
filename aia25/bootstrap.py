import os

os.environ.setdefault("OPENAI_AGENTS_DISABLE_TRACING", "1")  # Disable default OpenAI tracing
os.environ.setdefault("MLFLOW_DISABLE_TELEMETRY", "true")

import logging
import sys
from pathlib import Path

import mlflow
import requests
from agents import set_default_openai_api, set_default_openai_client
from openai import AsyncOpenAI

sys.path.append(str(Path(__file__).resolve().parent.parent))

logging.getLogger("openai.agents").setLevel(logging.CRITICAL)

# Set up defaults
custom_client = AsyncOpenAI(api_key=os.getenv("OPENROUTER_API_KEY"), base_url=os.getenv("BASE_URL"))
set_default_openai_client(custom_client)
set_default_openai_api("chat_completions")


# Activate MLFlow tracing if MLFlow is available
logger = logging.getLogger("chainlit")
mlflow_port = os.getenv("MLFLOW_PORT", "5001")

try:
    response = requests.get(f"http://localhost:{mlflow_port}/health", timeout=2)

    if response.status_code == 200:
        # Optional: enable auto tracing for OpenAI Agents SDK (if mlflow is running)
        mlflow.openai.autolog()
        mlflow.set_tracking_uri(f"http://localhost:{mlflow_port}")
        os.environ.setdefault("MLFLOW_TRACING_ENABLED", "True")
        logger.info("MLflow server is running, tracing is enabled.")
    else:
        os.environ.setdefault("MLFLOW_TRACING_ENABLED", "False")
        logger.warning("MLflow server is not running, tracing will be disabled.")
except requests.RequestException:
    os.environ.setdefault("MLFLOW_TRACING_ENABLED", "False")
    logger.warning("MLflow server is not running, tracing will be disabled.")
