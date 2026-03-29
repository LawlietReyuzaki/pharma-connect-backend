FROM python:3.11-slim

# Install nginx + system deps
RUN apt-get update && apt-get install -y nginx libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Flask app
COPY . .

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
