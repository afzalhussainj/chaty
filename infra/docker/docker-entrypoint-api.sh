#!/bin/sh
set -e
cd /app
retries=20
sleep_s=3
i=1
while [ "$i" -le "$retries" ]; do
  if alembic upgrade head; then
    break
  fi
  if [ "$i" -eq "$retries" ]; then
    echo "alembic upgrade head failed after ${retries} attempts"
    exit 1
  fi
  echo "alembic failed (attempt ${i}/${retries}); retrying in ${sleep_s}s..."
  sleep "$sleep_s"
  i=$((i + 1))
done
exec "$@"
