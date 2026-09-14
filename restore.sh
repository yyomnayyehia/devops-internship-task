#!/usr/bin/env bash
set -e

if [ ! -f "./postgres_backup.dump" ]; then
    echo "[FAIL] Backup file ./postgres_backup.dump not found!"
    exit 1
fi

echo "Starting PostgreSQL restore..."
docker exec -i postgres pg_restore -U barq_app -d barq_tasks --clean --if-exists < ./postgres_backup.dump

echo "[PASS] pg_restore ran successfully."

echo "Verifying restored data is actually queryable through the API..."
RESPONSE=$(curl -s http://127.0.0.1:8080/records)

if [ -z "$RESPONSE" ]; then
    echo "[FAIL] /records returned no response after restore."
    exit 1
fi

RECORD_COUNT=$(echo "$RESPONSE" | grep -o '"id"' | wc -l)

if [ "$RECORD_COUNT" -gt 0 ]; then
    echo "[PASS] Restore verified: /records returned $RECORD_COUNT record(s)."
    echo "$RESPONSE"
else
    echo "[FAIL] /records returned zero records after restore — restore may not have worked."
    exit 1
fi

echo "Redis persistence restores automatically from its AOF file when the container starts."
echo "Restore complete!"