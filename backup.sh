#!/usr/bin/env bash
set -e

echo "Starting PostgreSQL backup..."
docker exec postgres pg_dump -U barq_app -d barq_tasks -F c > ./postgres_backup.dump

echo "[PASS] PostgreSQL database backed up to ./postgres_backup.dump"

echo "Starting Redis backup..."
docker exec redis redis-cli SAVE

echo "[PASS] Redis data saved to persistent disk."
echo "Backup complete!"