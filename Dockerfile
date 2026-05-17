FROM python:3.11-slim

# Install nginx + system deps
RUN apt-get update && apt-get install -y nginx libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Flask app
COPY . .

# Build the catalog Chroma collection from medicines_export.json
# (Phase 1 Catalog Sub-Agent). GEMINI_API_KEY is passed as a build arg so the
# embedding step can run. If it's absent at build time, the step is skipped and
# the agent will fall back to the legacy keyword search at runtime.
ARG GEMINI_API_KEY=""
RUN if [ -n "$GEMINI_API_KEY" ]; then \
        GEMINI_API_KEY="$GEMINI_API_KEY" python scripts/build_catalog_embeddings.py --rebuild; \
    else \
        echo "WARN: GEMINI_API_KEY not provided to build; skipping embedding build (legacy fallback will be used)"; \
    fi

# Copy pre-built React apps (built by cloudbuild.yaml before Docker build)
# frontend build → static/frontend, admin build → static/admin-panel
RUN mkdir -p /var/www/frontend /var/www/admin

COPY static/frontend/ /var/www/frontend/
COPY static/admin-panel/ /var/www/admin/

# Nginx config
COPY nginx.conf /etc/nginx/sites-available/default
RUN rm -f /etc/nginx/sites-enabled/default && ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

ENV PORT=8080
EXPOSE 8080

COPY start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]
