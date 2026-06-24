#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/geekspace-webchat}"

cd "$APP_DIR"
git pull --ff-only
docker compose up -d --build
docker compose ps
curl -fsS http://127.0.0.1/api/health || true
echo
