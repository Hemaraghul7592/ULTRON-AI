#!/usr/bin/env bash
set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup-file>"
    echo "Example: $0 backups/ultron_db_20260720_120000.sql"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

if [[ "$BACKUP_FILE" == *.sql ]]; then
    echo "Restoring PostgreSQL database..."
    if [ -z "${DATABASE_URL:-}" ]; then
        echo "Error: DATABASE_URL is not set."
        exit 1
    fi
    psql "${DATABASE_URL#postgresql+asyncpg://}" < "$BACKUP_FILE"
    echo "PostgreSQL restore complete."
elif [[ "$BACKUP_FILE" == *.db ]]; then
    echo "Restoring SQLite database..."
    cp "$BACKUP_FILE" ultron.db
    echo "SQLite restore complete."
else
    echo "Error: Unknown backup format. Use .sql for PostgreSQL or .db for SQLite."
    exit 1
fi
