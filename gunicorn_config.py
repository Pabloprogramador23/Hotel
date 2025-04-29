"""
Configuração do Gunicorn para produção
"""
import multiprocessing
import os

# Diretório de trabalho
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

# Número de workers baseado no número de cores
workers = int(os.environ.get("GUNICORN_WORKERS", (multiprocessing.cpu_count() * 2) + 1))

# Tipo de worker
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "sync")

# Timeout em segundos
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))

# Máximo de requisições antes do restart do worker
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", 50))

# Log
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "-")  # - para stdout
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "-")    # - para stderr

# Configurações para manter o servidor rodando por longos períodos
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", 5))
worker_tmp_dir = os.environ.get("GUNICORN_WORKER_TMP_DIR", "/dev/shm")
worker_abort_on_error = True

# SSL (em produção, recomenda-se usar um proxy como Nginx para SSL)
# keyfile = os.environ.get("GUNICORN_SSL_KEYFILE")
# certfile = os.environ.get("GUNICORN_SSL_CERTFILE")