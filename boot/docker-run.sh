#!/bin/bash

source /opt/venv/bin/activate

cd /code
RUN_PORT=${PORT:-8000}
RUN_HOST=${HOST:-0.0.0.0}

# Create admin user if environment variables are set
if [ ! -z "$ADMIN_USERNAME" ] && [ ! -z "$ADMIN_EMAIL" ] && [ ! -z "$ADMIN_PASSWORD" ]; then
    echo "Creating admin user..."
    python cli.py
fi

gunicorn -k uvicorn.workers.UvicornWorker -b $RUN_HOST:$RUN_PORT --reload main:app