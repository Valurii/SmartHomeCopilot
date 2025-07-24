#!/usr/bin/env bash

# Deploys a test stack and triggers the nightly automation.
# Requires Docker and a valid $HASS_TOKEN for Home Assistant API access.

set -euo pipefail

STACK_NAME="smartcopilot_test"
STACK_FILE="docker-stack-smartcopilot.yml"
HASS_API="http://localhost:8123/api/"

# Deploy the stack
if ! docker stack deploy -c "$STACK_FILE" "$STACK_NAME"; then
  echo "Failed to deploy stack" >&2
  exit 1
fi

# Wait until Home Assistant API is reachable
MAX_RETRIES=30
until curl -sf -H "Authorization: Bearer $HASS_TOKEN" "$HASS_API" >/dev/null; do
  if (( MAX_RETRIES-- == 0 )); then
    echo "Home Assistant API did not respond in time" >&2
    docker stack rm "$STACK_NAME" >/dev/null 2>&1 || true
    echo "FAIL"
    exit 1
  fi
  echo "Waiting for Home Assistant..." >&2
  sleep 10
done

# Trigger nightly automation
curl -fsSL -H "Authorization: Bearer $HASS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST -d '{}' "${HASS_API}services/automation/trigger" \
  --data-urlencode 'entity_id=automation.smartcopilot_nightly'
RESULT=$?

# Remove the stack
docker stack rm "$STACK_NAME" >/dev/null 2>&1 || true

if [ $RESULT -eq 0 ]; then
  echo "OK"
else
  echo "FAIL"
fi

exit $RESULT
