"""
Gunicorn configuration for production.

Workers: min(4, cpu*2) to avoid CPU thrash on small boxes.
"""
import multiprocessing
import os

workers = min(4, max(1, multiprocessing.cpu_count() * 2))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "75"))
loglevel = os.getenv("LOG_LEVEL", "warning")

# Bind from env if provided
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

accesslog = os.getenv("GUNICORN_ACCESSLOG", "-") if os.getenv("ACCESS_LOG", "0") in ("1","true","True") else None
errorlog = "-"

