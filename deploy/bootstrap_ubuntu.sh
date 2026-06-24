#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/geekspace-webchat}"
REPO_URL="${REPO_URL:-https://github.com/qingqingcai23-max/geekspace-webchat.git}"

echo "[1/6] Installing base packages"
sudo apt update
sudo apt install -y ca-certificates curl git

if ! command -v docker >/dev/null 2>&1; then
  echo "[2/6] Installing Docker"
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
else
  echo "[2/6] Docker already installed"
fi

sudo mkdir -p "$(dirname "$APP_DIR")"
sudo chown "$USER":"$USER" "$(dirname "$APP_DIR")"

if [ ! -d "$APP_DIR/.git" ]; then
  echo "[3/6] Cloning project"
  git clone "$REPO_URL" "$APP_DIR"
else
  echo "[3/6] Project already exists, pulling latest code"
  git -C "$APP_DIR" pull --ff-only
fi

cd "$APP_DIR"

if [ ! -f .env ] && [ -f .env.example ]; then
  echo "[4/6] Creating .env from template"
  cp .env.example .env
fi

if grep -q "replace-with-your-real-key" .env 2>/dev/null; then
  cat <<'EOF'
[5/6] Please edit .env before the first real launch:
  nano .env

Replace:
  GEEKSPACE_API_KEY=replace-with-your-real-key

After saving, run:
  cd /opt/geekspace-webchat
  docker compose up -d --build
EOF
  exit 0
fi

echo "[5/6] Building and starting containers"
docker compose up -d --build

echo "[6/6] Health check"
sleep 3
curl -fsS http://127.0.0.1/api/health || true
echo
echo "Done. Open: http://<your-server-ip>/"
