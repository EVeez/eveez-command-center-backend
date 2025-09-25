How to profile quickly

1) Install deps:
   pip install -r requirements.txt

2) Run server (prod-like):
   uvicorn main:app --host 0.0.0.0 --port 8000

3) Run py-spy to sample hot endpoint for ~10s:
   py-spy record -o profile.svg --pid $(python -c "import psutil;print([p.pid for p in psutil.process_iter(['name']) if 'uvicorn' in (p.info.get('name') or '')][0])") --rate 100

Or simpler while curling:
   py-spy top --pid <PID>

Findings (local):
- High time in MySQL client when results not fully consumed. Fixed by buffered=True and connection pool.
- JSON serialization sizable; switched to ORJSON.
- Mongo list endpoints returned full documents; added projections to reduce payload.

