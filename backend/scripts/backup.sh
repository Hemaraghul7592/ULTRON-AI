#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

if grep -q "postgresql" <<< "${DATABASE_URL:-}"; then
    echo "Backing up PostgreSQL database..."
    pg_dump "${DATABASE_URL#postgresql+asyncpg://}" > "$BACKUP_DIR/ultron_db_$TIMESTAMP.sql"
    echo "Backup saved to: $BACKUP_DIR/ultron_db_$TIMESTAMP.sql"
else
    echo "Backing up SQLite database..."
    cp ultron.db "$BACKUP_DIR/ultron_db_$TIMESTAMP.db"
    echo "Backup saved to: $BACKUP_DIR/ultron_db_$TIMESTAMP.db"
fi

echo "Backup complete."
