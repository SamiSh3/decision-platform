#!/usr/bin/env bash
# Rebuild and restart the production stack, apply migrations, verify /health.
set -euo pipefail

cd "$(dirname "$0")/.."
compose="docker compose -f docker-compose.prod.yml"

$compose build api
$compose up -d db
$compose run --rm api alembic upgrade head
$compose up -d

for _ in $(seq 1 30); do
  if curl -fsS http://localhost:8000/health; then
    echo
    exit 0
  fi
  sleep 2
done

echo "Health check failed" >&2
$compose logs --tail 50 api >&2
exit 1
