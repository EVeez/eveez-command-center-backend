Production deployment on Ubuntu

Prereqs
- Python 3.10+
- virtualenv

Install
```bash
sudo apt update && sudo apt install -y python3-venv build-essential
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Run (Gunicorn + UvicornWorker)
```bash
export LOG_LEVEL=warning
export USE_ORJSON=1
gunicorn main:app -c gunicorn_conf.py
```

Local dev
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

systemd
- See deploy/systemd/service_app.service

Logging
- Gunicorn error log to stderr. Use journald or logrotate as per systemd defaults.

Tuning
- workers=min(4, cpu*2). Increase cautiously.
- Enable Redis cache: set ENABLE_REDIS_CACHE=1.

