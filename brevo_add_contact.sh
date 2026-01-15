#!/bin/bash

# Load .env file
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Argument: email
EMAIL="$1"

curl -s -X POST "https://api.brevo.com/v3/contacts" \
  -H "api-key: $BREVO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"updateEnabled\": true
  }"
