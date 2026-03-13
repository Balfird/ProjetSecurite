#!/bin/bash
set -e

DB_PATH="/root/SMTP_Relay/emails.db"
ARCHIVE_DIR="/root/SMTP_Relay/archives"
SCRIPT_DIR="/root/SMTP_Relay/scripts"
MAX_SIZE=$((1024 * 1024 * 1024)) # 1GB in bytes

mkdir -p "$ARCHIVE_DIR"

if [ -f "$DB_PATH" ]; then
    FILE_SIZE=$(stat -c%s "$DB_PATH")
    
    if [ "$FILE_SIZE" -gt "$MAX_SIZE" ]; then
        echo "[$(date)] Database size ($FILE_SIZE bytes) exceeds limit ($MAX_SIZE bytes). Initiating archive..."
        
        # 1. Stop Service
        echo "Stopping smtp-relay service..."
        systemctl stop smtp-relay
        
        # 2. Move Database
        TIMESTAMP=$(date +%d-%m-%y)
        ARCHIVE_DB="$ARCHIVE_DIR/emails.db.archived.$TIMESTAMP"
        mv "$DB_PATH" "$ARCHIVE_DB"
        echo "Moved database to $ARCHIVE_DB"
        
        # 3. Start Service (Creates new DB)
        echo "Restarting smtp-relay service..."
        systemctl start smtp-relay
        
        # 4. Convert to Excel
        EXCEL_FILE="$ARCHIVE_DIR/Export-mail-$TIMESTAMP.xlsx"
        echo "Converting to Excel: $EXCEL_FILE"
        python3 "$SCRIPT_DIR/archive_db.py" "$ARCHIVE_DB" "$EXCEL_FILE"
        
        # 5. Cleanup
        if [ -f "$EXCEL_FILE" ]; then
            echo "Excel exported successfully. Deleting archived DB file..."
            rm "$ARCHIVE_DB"
        else
            echo "ERROR: Excel file not found. Keeping archived DB file for safety."
        fi
        
        echo "Archive process completed."
    else
        echo "[$(date)] Database size ($FILE_SIZE bytes) is within limits."
    fi
else
    echo "Database file not found at $DB_PATH"
fi
