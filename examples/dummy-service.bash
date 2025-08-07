#!/bin/bash

# name: Dummy Service
# description: A dummy service for testing.
# version: 1
# schedule: *:0/1

# --- Constants ---
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo "$TIMESTAMP, $STATUS_OK"
