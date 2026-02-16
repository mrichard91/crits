#!/bin/sh
set -e

SSL_DIR="/etc/nginx/ssl"
CERT="$SSL_DIR/cert.pem"
KEY="$SSL_DIR/key.pem"

if [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
    echo "Installing openssl..."
    apk add --no-cache openssl >/dev/null 2>&1
    echo "Generating self-signed SSL certificate..."
    mkdir -p "$SSL_DIR"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY" \
        -out "$CERT" \
        -subj "/C=US/ST=Dev/L=Dev/O=CRITs/CN=localhost"
    echo "SSL certificate generated."
fi

exec nginx -g 'daemon off;'
