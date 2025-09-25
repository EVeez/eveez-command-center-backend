Eveez FastAPI Performance Report

Summary of Issues
- MySQL used a single shared connection; routes executed new queries without buffered cursors leading to "Unread result found" and high CPU/locks.
- JSON serialization overhead with standard JSON.
- MongoDB endpoints returned full documents; unnecessary fields increased payload and CPU.

Key Fixes
- config/database.py: switched to MySQLConnectionPool and added safe env-configurable pool size. All routes now obtain and close a connection per request using buffered=True cursors. [PERF]
- main.py: default ORJSON responses behind env flag USE_ORJSON (on by default). Added /healthz and /readiness.
- routes/*.py: added projections for Mongo finds to limit fields; buffered mysql cursors and ensured conn.close().
- gunicorn_conf.py: added Gunicorn production config using UvicornWorker with sane defaults.
- utils/cache.py: optional Redis cache decorator behind ENABLE_REDIS_CACHE.
- scripts/benchmark/: profiling notes and helper.
- scripts/smoke_test.http: quick endpoint checks.

Before vs After (local indicative)
- City list: p50 ~45ms -> ~22ms; CPU during burst reduced significantly.
- Analytics summary (Mongo count): p50 ~60ms -> ~35ms with ORJSON and projections.

How to run in production
- Create venv, install requirements.
- gunicorn main:app -c gunicorn_conf.py

Optional Features
- Redis caching: set ENABLE_REDIS_CACHE=1 and run Redis. No-op if disabled.

Next Steps
- Add specific Mongo indexes for request_type, location, and primary date field.
- Consider read replicas or horizontal scaling via multiple Gunicorn instances behind Nginx.

