#!/bin/bash
# Start gunicorn in background on port 5000
gunicorn --bind 127.0.0.1:5000 --workers 2 --threads 4 --timeout 120 "app:create_app()" &

# Start nginx in foreground (keeps container alive)
nginx -g "daemon off;"
