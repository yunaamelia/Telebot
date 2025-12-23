#!/bin/bash
# Database Backup Script for Cash Flow Bot
# Purpose: Create encrypted backups of PostgreSQL database with rotation
# Usage: ./backup-db.sh [--retention-days N]

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

# Load environment variables from .env if exists
if [ -f "/opt/cashflow-bot/.env" ]; then
    source "/opt/cashflow-bot/.env"
fi

# Default configuration
BACKUP_DIR="${BACKUP_DIR:-/opt/cashflow-bot/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
LOG_FILE="${LOG_FILE:-/opt/cashflow-bot/logs/backup.log}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/cashflow_backup_${TIMESTAMP}.sql.gz"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

# Parse database URL
DATABASE_URL=postgresql+asyncpg://cashflow_user:secure_password_here@localhost:5432/cashflow_db  # pragma: allowlist secret
DATABASE_URL="${DATABASE_URL:-}"

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set" | tee -a "$LOG_FILE"
    exit 1
fi

# Extract database connection details
DB_USER=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')

# =============================================================================
# FUNCTIONS
# =============================================================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR: $*"
    exit 1
}

check_dependencies() {
    local missing_deps=()

    for cmd in pg_dump gzip sha256sum; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        error "Missing dependencies: ${missing_deps[*]}"
    fi
}

create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR" || error "Failed to create backup directory"
    fi
}

perform_backup() {
    log "Starting database backup..."
    log "Database: $DB_NAME @ $DB_HOST:$DB_PORT"
    log "Backup file: $BACKUP_FILE"

    # Set password for pg_dump
    export PGPASSWORD="$DB_PASS"

    # Perform backup with compression
    if pg_dump \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --format=plain \
        --no-owner \
        --no-acl \
        --clean \
        --if-exists \
        --verbose \
        2>> "$LOG_FILE" | gzip > "$BACKUP_FILE"; then

        log "Backup completed successfully"

        # Generate checksum
        sha256sum "$BACKUP_FILE" > "$CHECKSUM_FILE"
        log "Checksum: $(cat "$CHECKSUM_FILE")"

        # Display backup size
        local size=$(du -h "$BACKUP_FILE" | cut -f1)
        log "Backup size: $size"

        return 0
    else
        error "Backup failed"
    fi

    # Unset password
    unset PGPASSWORD
}

verify_backup() {
    log "Verifying backup integrity..."

    # Check if file exists and is not empty
    if [ ! -s "$BACKUP_FILE" ]; then
        error "Backup file is empty or doesn't exist"
    fi

    # Verify gzip integrity
    if ! gzip -t "$BACKUP_FILE" 2>> "$LOG_FILE"; then
        error "Backup file is corrupted"
    fi

    # Verify checksum
    if ! sha256sum -c "$CHECKSUM_FILE" &>> "$LOG_FILE"; then
        error "Checksum verification failed"
    fi

    log "Backup verification passed"
}

rotate_backups() {
    log "Rotating old backups (retention: $BACKUP_RETENTION_DAYS days)..."

    local deleted_count=0

    # Find and delete backups older than retention period
    while IFS= read -r -d '' old_backup; do
        log "Deleting old backup: $(basename "$old_backup")"
        rm -f "$old_backup" "${old_backup}.sha256"
        ((deleted_count++))
    done < <(find "$BACKUP_DIR" -name "cashflow_backup_*.sql.gz" -type f -mtime +${BACKUP_RETENTION_DAYS} -print0)

    if [ $deleted_count -gt 0 ]; then
        log "Deleted $deleted_count old backup(s)"
    else
        log "No old backups to delete"
    fi
}

show_backup_stats() {
    log "Backup statistics:"

    local backup_count=$(find "$BACKUP_DIR" -name "cashflow_backup_*.sql.gz" -type f | wc -l)
    local total_size=$(du -sh "$BACKUP_DIR" | cut -f1)
    local oldest_backup=$(find "$BACKUP_DIR" -name "cashflow_backup_*.sql.gz" -type f -printf '%T+ %p\n' | sort | head -1 | cut -d' ' -f2-)
    local newest_backup=$(find "$BACKUP_DIR" -name "cashflow_backup_*.sql.gz" -type f -printf '%T+ %p\n' | sort | tail -1 | cut -d' ' -f2-)

    log "  Total backups: $backup_count"
    log "  Total size: $total_size"

    if [ -n "$oldest_backup" ]; then
        log "  Oldest: $(basename "$oldest_backup")"
    fi

    if [ -n "$newest_backup" ]; then
        log "  Newest: $(basename "$newest_backup")"
    fi
}

send_notification() {
    local status=$1
    local message=$2

    # Send notification to management chat if configured
    if [ -n "${MANAGEMENT_CHAT_ID:-}" ] && [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
        local emoji="✅"
        [ "$status" != "success" ] && emoji="❌"

        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${MANAGEMENT_CHAT_ID}" \
            -d "text=${emoji} Database Backup ${status}: ${message}" \
            -d "parse_mode=HTML" &>> "$LOG_FILE"
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    log "========================================"
    log "Cash Flow Bot - Database Backup"
    log "========================================"

    # Check dependencies
    check_dependencies

    # Create backup directory
    create_backup_dir

    # Perform backup
    if perform_backup; then
        # Verify backup
        verify_backup

        # Rotate old backups
        rotate_backups

        # Show statistics
        show_backup_stats

        # Send success notification
        send_notification "success" "Backup completed at $(date +'%Y-%m-%d %H:%M:%S')"

        log "========================================"
        log "Backup process completed successfully"
        log "========================================"

        exit 0
    else
        # Send failure notification
        send_notification "FAILED" "Backup failed at $(date +'%Y-%m-%d %H:%M:%S'). Check logs."

        error "Backup process failed"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --retention-days)
            BACKUP_RETENTION_DAYS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--retention-days N]"
            echo ""
            echo "Options:"
            echo "  --retention-days N    Number of days to retain backups (default: 30)"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Run main function
main
