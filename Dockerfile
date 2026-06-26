FROM node:22-bookworm-slim AS node_runtime

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    GEEKSPACE_VAULT_DIR=/app/runtime/xuanxue-knowledge-vault

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=node_runtime /usr/local/bin/node /usr/local/bin/node
COPY --from=node_runtime /app/node_modules ./node_modules
COPY . .

EXPOSE 8080

CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT:-8080} wsgi:app"]
