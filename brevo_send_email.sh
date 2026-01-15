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

# Build recipients array as JSON using jq
TO_ARRAY=$(echo "$TO_EMAILS" | tr ',' '\n' | jq -R '{email: .}' | jq -s '.')

# Build JSON payload with proper escaping
JSON_PAYLOAD=$(jq -n \
  --arg from_email "$MAIL_FROM" \
  --arg subject "$SUBJECT" \
  --arg body "$BODY" \
  --argjson to "$TO_ARRAY" \
  '{
    sender: {email: $from_email, name: "JobFlow"},
    to: $to,
    subject: $subject,
    textContent: $body
  }')

curl -s -X POST "https://api.brevo.com/v3/smtp/email" \
  -H "api-key: $BREVO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD"
