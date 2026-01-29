#!/bin/bash

redis-server &
uv run celery -A make_celery worker --concurrency=8 --loglevel INFO &
uv run python3 ./cleanup_jobs.py &
uv run gunicorn --worker-class gevent --workers 4 "fermo_gui:create_app()" --bind "0.0.0.0:8001"
