#!/bin/bash

# --- Manifest --- #
# name: ZFS Zpool Health
# description: Checks the health of ZFS zpools.
# version: 1.0
# schedule: *-*-* 06:00:00
# timeout: 300000

# --- Standard Constants --- #
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
STATUS_ERROR="ERROR"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configurations --- #
POOL_NAME="data_pool"

# --- Dependencies --- #
# zpool

# --- Main --- #
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
ZPOOL_STATUS_OUTPUT=$(zpool status "$POOL_NAME")
FINAL_POOL_STATUS=$(echo "$ZPOOL_STATUS_OUTPUT" | grep "state:" | awk '{print $2}')
FINAL_POOL_ERRORS=$(echo "$ZPOOL_STATUS_OUTPUT" | grep "errors:" | sed -E 's/errors: (.*)/\1/')

# Check for CKSUM errors. We look at the 5th column (CKSUM) for any non-zero value.
# We skip the header line 'NAME...CKSUM' and the pool name line itself.
CKSUM_ERRORS=$(echo "$ZPOOL_STATUS_OUTPUT" | awk '
    /config:/ { in_config=1; next }
    /errors:/ { in_config=0; next }
    in_config && NF >= 5 && $1 != "NAME" && $5 != "CKSUM" && $5 + 0 > 0 {
        print $1 " has " $5 " CKSUM errors";
    }
' | head -n 1)

# We also need to make sure the CHSUM_ERRORS is a single line for the SSI logs
# We can keep only the first print line. We assume the user will check for CKSUM errors
# manually on the pool after we inform for a CKSUM error.
CKSUM_ERRORS=$(echo "$CKSUM_ERRORS" | head -n 1)

if [ "$FINAL_POOL_STATUS" != "ONLINE" ]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, ZFS pool '$POOL_NAME' is in state: $FINAL_POOL_STATUS. Errors: $FINAL_POOL_ERRORS"
    exit 1
elif [ "$FINAL_POOL_ERRORS" != "No known data errors" ]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, ZFS pool '$POOL_NAME' has errors: $FINAL_POOL_ERRORS"
    exit 1
elif [ -n "$CKSUM_ERRORS" ]; then
    echo "$TIMESTAMP, $STATUS_WARNING, ZFS pool '$POOL_NAME' has CKSUM errors. Details: $CKSUM_ERRORS"
    exit 0
else
    echo "$TIMESTAMP, $STATUS_OK, ZFS pool '$POOL_NAME' is healthy."
    exit 0
fi
