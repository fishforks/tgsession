#!/bin/sh
set -e

# Defaults
export TZ=${TZ:-Asia/Shanghai}
export DOMAIN=${DOMAIN:-localhost}
export BACKEND_HOST=${BACKEND_HOST:-127.0.0.1}
export BACKEND_PORT=${BACKEND_PORT:-8000}
export WORKERS=${WORKERS:-2}

echo "Starting TGSession integrated service..."
echo "- Domain: ${DOMAIN}"
echo "- Backend: ${BACKEND_HOST}:${BACKEND_PORT} (workers=${WORKERS})"
echo "- Frontend dir: /app/frontend/dist"

# Prepare dirs
mkdir -p /app/data /app/logs /var/log/nginx

# Detect SSL
SSL_AVAILABLE=false
if [ -f "/app/data/ssl/fullchain.pem" ] && [ -f "/app/data/ssl/privkey.pem" ]; then
    SSL_AVAILABLE=true
    echo "SSL certs detected - HTTPS will be enabled"
else
    echo "No SSL certs found - serving HTTP only"
fi

# Remove default nginx site if present
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm -f /etc/nginx/sites-enabled/default
fi

# Generate nginx config
cat > /etc/nginx/conf.d/default.conf << EOF
# HTTP server
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 50M;
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

$(if [ "$SSL_AVAILABLE" = true ]; then
    echo "    return 301 https://\$host\$request_uri;"
    echo "}"
    echo ""
    echo "# HTTPS server"
    echo "server {"
    echo "    listen 443 ssl http2;"
    echo "    server_name ${DOMAIN};"
    echo ""
    echo "    ssl_certificate /app/data/ssl/fullchain.pem;"
    echo "    ssl_certificate_key /app/data/ssl/privkey.pem;"
    echo "    ssl_protocols TLSv1.2 TLSv1.3;"
    echo "    ssl_prefer_server_ciphers on;"
    echo "    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;"
    echo "    add_header Strict-Transport-Security \"max-age=31536000; includeSubDomains\" always;"
    echo "    add_header X-Content-Type-Options nosniff;"
    echo "    add_header X-Frame-Options SAMEORIGIN;"
    echo "    add_header X-XSS-Protection \"1; mode=block\";"
else
    echo "    # HTTP-only configuration"
fi)

    # Health endpoint (API)
    location = /health {
        proxy_pass http://${BACKEND_HOST}:${BACKEND_PORT}/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout 10s;
        proxy_send_timeout 5s;
        proxy_buffering off;
    }

    # API endpoints
    location = /get_session {
        proxy_pass http://${BACKEND_HOST}:${BACKEND_PORT}/get_session;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    location = /check_qr_status {
        proxy_pass http://${BACKEND_HOST}:${BACKEND_PORT}/check_qr_status;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location = /active_sessions {
        proxy_pass http://${BACKEND_HOST}:${BACKEND_PORT}/active_sessions;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location ^~ /cleanup {
        proxy_pass http://${BACKEND_HOST}:${BACKEND_PORT};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root /app/frontend/dist;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
        add_header X-Content-Type-Options nosniff;
    }

    # SPA routing
    location / {
        root /app/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
        location ~* \.html$ {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }
    }
}
EOF

echo "Nginx config generated."

# Start backend (uvicorn) in background
echo "Starting FastAPI backend..."
python -m uvicorn TGSession.api:app --host ${BACKEND_HOST} --port ${BACKEND_PORT} --workers ${WORKERS} > /app/logs/backend.log 2>&1 &

# Wait for backend health
echo "Waiting for backend to become healthy..."
for i in $(seq 1 40); do
    if curl -fsS http://${BACKEND_HOST}:${BACKEND_PORT}/health >/dev/null 2>&1; then
        echo "Backend is healthy."
        break
    fi
    echo "... ($i/40)"
    sleep 1
done

if ! curl -fsS http://${BACKEND_HOST}:${BACKEND_PORT}/health >/dev/null 2>&1; then
    echo "ERROR: Backend failed to start. Logs:" >&2
    tail -n 200 /app/logs/backend.log || true
    exit 1
fi

echo "Starting Nginx..."
nginx -t && nginx -g "daemon off;"


