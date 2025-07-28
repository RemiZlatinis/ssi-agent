#!/bin/bash

# name: This is a Service Example
# description: Checking for system updates on Debian/Ubuntu
# version: 1.0
# interval: 01 * * * *
# timeout: 20 (Seconds - Optional)

# --- Description ---
# The following script checks for updates on a Debian system
# Returns ["ok", "System is up to date"] if there are no updates
# Returns ["update", "X available updates"] if there are updates

# --- Status Constants ---
STATUS_OK="OK"
STATUS_UPDATE="UPDATE"
STATUS_WARNING="WARNING"
STATUS_FAILURE="FAILURE"

# --- Configuration ---
# You can customize the output messages here if needed.
MSG_OK="System is up to date"
MSG_UPDATE_AVAILABLE="available updates"

# --- Script Logic ---
# Update the package list (without upgrading)
apt-get update > /dev/null 2>&1

# Check for upgradable packages
upgradable_packages=$(apt list --upgradable 2>/dev/null | wc -l)

# Remove the header line from the count
upgradable_packages=$((upgradable_packages - 1))

# Check if there are any upgradable packages
if [ "$upgradable_packages" -gt 0 ]; then
  # If there are updates, output "update" and the number of updates
  echo "$STATUS_UPDATE, $upgradable_packages $MSG_UPDATE_AVAILABLE"
else
  # If there are no updates, output "ok" and the message
  echo "$STATUS_OK, $MSG_OK"
fi

exit 0 # Success
