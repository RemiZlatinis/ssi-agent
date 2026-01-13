#!/bin/bash

# --- Manifest --- #
# name: API Health
# description: Checks the health of an API that has a health check endpoint
# version: 1.0
# schedule: *:0/01:00
# timeout: 10

# --- Overview --- #
# The following script calls the health check endpoint at the configured URL
# and checks for the expected response.
# Returns "OK" "API is healthy" if all checks are fine.
# Returns "WARNING" "Health check failed" if any check fails or the request fails.
# Returns "FAILURE" "API is unreachable" if the api is unreachable.

# --- Standard Constants --- #
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configurations --- #
URL="https://api.service-status-indicator.com/api/health/"
read -r -d '' EXPECTED_RESPONSE << 'EOF'
{"Cache backend: default": "working",
 "DatabaseBackend": "working",
 "DatabaseBackend[default]": "working",
 "MigrationsHealthCheck": "working"}
EOF

# --- Dependencies --- #
# curl
# sed
# tr

# --- Main --- #
# Fetch HTTP status first to check reachability
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Accept: application/json" "$URL" 2>/dev/null)

if [ "$HTTP_CODE" != "200" ]; then
    echo "$TIMESTAMP, $STATUS_FAILURE, API is unreachable (code: $HTTP_CODE)"
    exit 1
fi

# Fetch the response body
RESPONSE=$(curl -s -H "Accept: application/json" "$URL" 2>/dev/null)

# Normalize by trimming whitespace and newlines for comparison
NORMALIZED_RESPONSE=$(echo "$RESPONSE" | tr -d '\n\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
NORMALIZED_EXPECTED=$(echo "$EXPECTED_RESPONSE" | tr -d '\n\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

# Check if response matches expected JSON exactly (after normalization)
if [[ "$NORMALIZED_EXPECTED" == "$NORMALIZED_RESPONSE" ]]; then
    echo "$TIMESTAMP, $STATUS_OK, API is healthy"
else
    echo "$TIMESTAMP, $STATUS_WARNING, Health check failed (response mismatch)"
    echo "Expected: $NORMALIZED_EXPECTED"
    echo "Got: $NORMALIZED_RESPONSE"
fi
