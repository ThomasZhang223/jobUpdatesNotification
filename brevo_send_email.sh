#!/bin/bash

# Load .env file
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Arguments: to_emails (comma-separated), subject, body
TO_EMAILS="$1"
SUBJECT="$2"
BODY="$3"

# Build recipients array
TO_ARRAY=$(echo "$TO_EMAILS" | sed 's/,/\"},\{\"email\":\"/g' | sed 's/^/{\"email\":\"/' | sed 's/$/\"}/')

curl -s -X POST "https://api.brevo.com/v3/smtp/email" \
  -H "api-key: $BREVO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"sender\": {
      \"email\": \"$MAIL_FROM\",
      \"name\": \"JobFlow\"
    },
    \"to\": [$TO_ARRAY],
    \"subject\": \"$SUBJECT\",
    \"textContent\": \"$BODY\"
  }"
