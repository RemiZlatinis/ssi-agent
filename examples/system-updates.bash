#!/bin/bash

# name: System Updates
# description: Checking for system updates on Debian/Ubuntu
# version: 1.0
# schedule: *:0/01:00
# timeout: 20

# --- Description ---
# The following script checks for updates on a Debian system
# Returns ["ok", "System is up to date"] if there are no updates
# Returns ["update", "X available updates"] if there are updates

# --- Constants ---
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# --- Configuration ---
# You can customize the output messages here if needed.
MSG_OK="System is up to date"
MSG_UPDATE_AVAILABLE="available updates"
MSG_SECURITY_UPDATES="security updates"

# --- Script Logic ---
# Check for both standard and security updates
updates=$(/usr/lib/update-notifier/apt-check 2>&1)

# apt-check outputs two numbers separated by a semicolon:
# standard_updates;security_updates
IFS=';' read -ra update_array <<< "$updates"
total_updates=${update_array[0]}
security_updates=${update_array[1]}

# Check if there are any updates
if [ "$total_updates" -gt 0 ]; then
  # If there are updates, output the count for both types
  echo "$TIMESTAMP, $STATUS_UPDATE, $total_updates $MSG_UPDATE_AVAILABLE ($security_updates $MSG_SECURITY_UPDATES)"
else
  # If there are no updates, output "ok"
  echo "$TIMESTAMP, $STATUS_OK, $MSG_OK"
fi

exit 0 # Success
