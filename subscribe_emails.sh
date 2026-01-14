#!/bin/bash

BASE_URL="https://jobupdatesnotification.onrender.com"

EMAILS=(
    "lishawn81@gmail.com"
    "yihanhon@usc.edu"
    "thomaszhang475178@gmail.com"
)

for email in "${EMAILS[@]}"; do
    echo "Subscribing: $email"
    curl -X POST "$BASE_URL/subscribe/$email"
    echo -e "\n"
done
