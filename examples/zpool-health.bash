#!/bin/bash

# name: ZFS Zpool Health
# description: Checks the health of ZFS zpools.
# version: 1.0
# schedule: *-*-* 06:00:00
# timeout: 300000

# --- Constants ---
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
STATUS_ERROR="ERROR"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configuration ---
POOL_NAME="data_pool"

# --- Script Logic ---
# Check if zpool command is available
if ! command -v zpool &> /dev/null
then
    echo "$TIMESTAMP, $STATUS_FAILURE, zpool command not found. Please ensure ZFS is installed."
    exit 1
fi

# Check if the specified pool exists
if ! zpool list "$POOL_NAME" &> /dev/null; then
    echo "$TIMESTAMP, $STATUS_ERROR, ZFS pool '$POOL_NAME' not found."
    exit 1
fi

# Start the scrub
if ! zpool scrub "$POOL_NAME" &> /dev/null; then
    # Check if scrub is already in progress
    if zpool status "$POOL_NAME" | grep -q 'scrub in progress'; then
        echo "$TIMESTAMP, $STATUS_WARNING, Scrub already in progress on pool '$POOL_NAME'."
    # else report failure to start scrub
    else
        echo "$TIMESTAMP, $STATUS_FAILURE, Failed to initiate scrub on pool '$POOL_NAME'."
        exit 1
    fi
fi

# Echo the status of the scrub as UPDATE every 3 seconds until it completes
while true; do
    SCRUB_STATUS=$(zpool status "$POOL_NAME" | grep 'scrub in progress')
    if [ -n "$SCRUB_STATUS" ]; then
        SCRUB_DETAILS=$(zpool status "$POOL_NAME" | grep -A 2 'scrub in progress' | tail -n 1)
        PROGRESS=$(echo "$SCRUB_DETAILS" | sed -E 's/.*, (.*), (.*)/\1, \2/')
        echo "$TIMESTAMP, $STATUS_UPDATE, Scrub in progress $PROGRESS."
        sleep 3
    else
        break
    fi
done

# Check final zpool status after scrub completes
FINAL_POOL_STATUS=$(zpool status "$POOL_NAME" | grep "state:" | awk '{print $2}')
FINAL_POOL_ERRORS=$(zpool status "$POOL_NAME" | grep "errors:" | sed -E 's/errors: (.*)/\1/')

if [ "$FINAL_POOL_STATUS" != "ONLINE" ]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, ZFS pool '$POOL_NAME' is in state: $FINAL_POOL_STATUS. Errors: $FINAL_POOL_ERRORS"
    exit 1
elif [ "$FINAL_POOL_ERRORS" != "No known data errors" ]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, ZFS pool '$POOL_NAME' has errors: $FINAL_POOL_ERRORS"
    exit 1
else
    echo "$TIMESTAMP, $STATUS_OK, ZFS pool '$POOL_NAME' is healthy."
    exit 0
fi
