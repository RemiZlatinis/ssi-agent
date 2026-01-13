#!/bin/bash

# --- Manifest --- #
# name: Daily Backup Snapshot Verifier
# description: Checks if a snapshot has been created for today.
# version: 1.0
# schedule: 0/6:00:00
# timeout: 10

# --- Overview --- #
# The following script lists the ZFS snapshots and checks if the expected snapshot is present.
# This doesn't verify if the backup is accurate or not. Only if the expected snapshot is present.
# Returns "OK" "Latest snapshot [YYYY-MM-DD HH:MM:SS]" if the latest snapshot is today.
# Returns "WARNING" "Latest snapshot [YYYY-MM-DD HH:MM:SS]" if latest snapshot is yesterday.
# Returns "FAILURE" "Multiple snapshots are missing" if latest snapshot is not today or yesterday.


# --- Standard Constants --- #
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configurations --- #
BACKUP_DIR="data_pool/backups/root-backup"

# --- Dependencies --- #
# zfs

# --- Main --- #
# List snapshot exact date-times for the backup directory
# -H: No header
# -o: Output fields
# -t snapshot: Only snapshots
# -s creation: Sort by creation time (newest last)
# -p: Display numbers in parsable (exact) values
SNAPSHOTS=$(zfs list -t snapshot -H -o creation -s creation -p "$BACKUP_DIR" 2>/dev/null)

# In case we have no snapshots at all
if [ -z "$SNAPSHOTS" ]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, There is no backup snapshot!"
    exit 1
fi

# Get the latest snapshot datetime (last line)
LATEST=$(echo "$SNAPSHOTS" | tail -n 1)
LATEST_FORMATTED=$(date -d "@$LATEST" +"%Y-%m-%d %H:%M:%S" 2>/dev/null)

# Calculate the age of the snapshots in seconds
NOW=$(date +%s)
AGE=$((NOW - LATEST))

# If the latest snapshot datetime is less then a day
if [ "$AGE" -lt 86400 ]; then
    echo "$TIMESTAMP, $STATUS_OK, Latest snapshot ($LATEST_FORMATTED)"

# If the latest snapshot datetime is yesterday
elif [ "$AGE" -lt 172800 ]; then
    echo "$TIMESTAMP, $STATUS_WARNING, Latest snapshot $LATEST_FORMATTED"

# If the latest snapshot datetime is more then 2 days old
else
    echo "$TIMESTAMP, $STATUS_FAILURE, Multiple snapshots are missing! (Latest snapshot: $LATEST_FORMATTED)"
fi
