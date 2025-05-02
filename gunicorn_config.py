"""Configuração do Gunicorn para o projeto Hotel HMS."""
import os
import multiprocessing

# Bind
bind = "0.0.0.0:8000"

# Número de workers - recomendado: (2 x núcleos) + 1
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Número de threads por worker
threads = int(os.environ.get("GUNICORN_THREADS", 1))

# Tipo de worker
worker_class = "gthread"  # Usar 'uvicorn.workers.UvicornWorker' para ASGI

# Timeout (segundos)
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 30))

# Máximo de conexões pendentes
backlog = int(os.environ.get("GUNICORN_BACKLOG", 2048))

# Máximo de requisições antes de reiniciar um worker
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", 50))

# Keepalive (segundos)
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", 2))

# Log
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")

# Preload app (melhor performance, mas mais uso de memória)
preload_app = os.environ.get("GUNICORN_PRELOAD_APP", "true").lower() == "true"

# Tamanho do buffer de requisição
limit_request_line = int(os.environ.get("GUNICORN_LIMIT_REQUEST_LINE", 4094))
limit_request_fields = int(os.environ.get("GUNICORN_LIMIT_REQUEST_FIELDS", 100))
limit_request_field_size = int(os.environ.get("GUNICORN_LIMIT_REQUEST_FIELD_SIZE", 8190))