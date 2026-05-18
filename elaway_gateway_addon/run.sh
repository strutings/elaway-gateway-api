#!/bin/sh

echo "Henter konfigurasjon fra Home Assistant..."
export ELAWAY_USER=$(jq --raw-output '.elaway_user' /data/options.json)
export ELAWAY_PASSWORD=$(jq --raw-output '.elaway_password' /data/options.json)
export ELAWAY_CLIENT_ID=$(jq --raw-output '.elaway_client_id' /data/options.json)
export ELAWAY_CLIENT_SECRET=$(jq --raw-output '.elaway_client_secret' /data/options.json)
export CLIENT_ID=$(jq --raw-output '.client_id' /data/options.json)
export PORT=$(jq --raw-output '.port' /data/options.json)

echo "Starter Elaway Gateway API..."

# Gå til app-mappen på innsiden av imaget ditt
cd /app

# Start Node med den nøyaktige stien fra din originale Dockerfile
exec node dist/src/main.js
