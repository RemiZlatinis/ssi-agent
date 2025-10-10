#!/bin/bash

# name: BTRFS Scrub
# description: Initiates a BTRFS scrub on a filesystem, reports its progress, and provides a final status.
# version: 1.0
# schedule: *-*-* 05:00:00
# timeout: 1800

# --- Description --- #
# This script manages and monitors BTRFS filesystem scrubs for a specified mount point.
#
# It performs the following actions:
# 1. Ensures that a scrub is running. If no scrub is active (i.e., the last one
#    was finished, cancelled, or none has ever run), it initiates a new one.
# 2. While the scrub is in progress, it periodically reports the status,
#    completion percentage, and estimated time remaining.
# 3. Once the scrub completes, it checks the final result. It will report success
#    if no errors were found, a warning if the scrub was interrupted, or a
#    failure if data errors were detected.

# --- Constants ---
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
STATUS_ERROR="ERROR"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configuration ---
MOUNT_POINT="/"
INTERNAL_INTERVAL=3

# --- Script Logic ---
# Verify the mount point exists.
if [ ! -d "$MOUNT_POINT" ]; then
    echo "$(date +"%Y-%m-%d %H:%M:%S"), ERROR, Mount point $MOUNT_POINT does not exist."
    exit 1
fi

# Verify the mount point is BTRFS.
if ! mount | grep -q " on $MOUNT_POINT type btrfs "; then
    echo "$TIMESTAMP, $STATUS_ERROR, Mount point $MOUNT_POINT is not a BTRFS filesystem."
    exit 1
fi

# Check if btrfs command is available
if ! command -v btrfs &> /dev/null; then
    echo "$TIMESTAMP, $STATUS_FAILURE, btrfs command not found. Please ensure btrfs-progs is installed."
    exit 1
fi

SCRUB_STATUS_OUTPUT=$(btrfs scrub status "$MOUNT_POINT" 2>/dev/null)
CURRENT_SCRUB_STATE=$(echo "$SCRUB_STATUS_OUTPUT" | grep '^Status:' | awk '{print $2}')

# If the current scrub state is not "running" (e.g., it's "finished", "cancelled", or no scrub has run yet/output is empty)
if [ "$CURRENT_SCRUB_STATE" != "running" ]; then
    if btrfs scrub start "$MOUNT_POINT" &> /dev/null; then
        echo "$TIMESTAMP, $STATUS_UPDATE, Started a new BTRFS scrub on '$MOUNT_POINT'."
    else
        # This block is reached if 'btrfs scrub start' command itself fails.
        # This could be due to various reasons, including:
        # - A scrub is actually running but the initial status check was flawed/out of sync.
        # - The filesystem is in a bad state.
        # - Permissions issues (though 'sudo' is implied for btrfs commands).
        echo "$TIMESTAMP, $STATUS_FAILURE, Failed to start a new BTRFS scrub on '$MOUNT_POINT'. Current detected state: '$CURRENT_SCRUB_STATE'."
        exit 1 # Exit if we fail to start the scrub
    fi
else
    echo "$TIMESTAMP, $STATUS_UPDATE, Scrub already in progress on '$MOUNT_POINT'."
fi

# Monitor and echo the scrub status until it completes
while true; do
    SCRUB_OUTPUT=$(btrfs scrub status "$MOUNT_POINT")
    STATUS=$(echo "$SCRUB_OUTPUT" | grep '^Status:' | awk '{print $2}')
    TIME_LEFT=$(echo "$SCRUB_OUTPUT" | grep '^Time left:' | awk '{print $3}')
    PROGRESS=$(echo "$SCRUB_OUTPUT" | grep '^Bytes scrubbed:' | sed -E 's/^.*\(//; s/%\)$//')

    # Setup just started values.
    if [ -z "$STATUS" ]; then
        STATUS="starting"
    fi
    if [ -z "$PROGRESS" ]; then
        PROGRESS="0"
    fi
    if [ -z "$TIME_LEFT" ]; then
        TIME_LEFT="calculating"
    fi

    # If scrub finished of cancelled exit the loop
    if [[ "$STATUS" == "finished" || "$STATUS" == "cancelled" ]]; then
        break
    fi

    echo "$TIMESTAMP, $STATUS_UPDATE, Scrub is $STATUS. Progress: $PROGRESS%, Time left: $TIME_LEFT."
    sleep "$INTERNAL_INTERVAL"
done

# Check the final status
FINAL_STATUS=$(btrfs scrub status -R "$MOUNT_POINT")

if echo "$FINAL_STATUS" | grep -q "errors: 0"; then
    echo "$TIMESTAMP, $STATUS_OK, BTRFS scrub on '$MOUNT_POINT' finished with no errors."
    exit 0
elif echo "$FINAL_STATUS" | grep -q "interrupted"; then
    echo "$TIMESTAMP, $STATUS_WARNING, BTRFS scrub on '$MOUNT_POINT' was interrupted."
    exit 1
else
    ERRORS=$(echo "$FINAL_STATUS" | grep "errors:" | sed 's/^[[:space:]]*//')
    echo "$TIMESTAMP, $STATUS_FAILURE, BTRFS scrub on '$MOUNT_POINT' finished with errors: $ERRORS"
    exit 1
fi
