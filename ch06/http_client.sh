#!/usr/bin/env bash
set -euo pipefail

if ! command -v curl >/dev/null 2>&1; then
    printf 'This demo requires curl.\n' >&2
    exit 127
fi

base_url="http://127.0.0.1:8000"

printf 'GET request and response:\n'
curl --include "$base_url/catalog"

printf '\nPOST request and response:\n'
curl --include \
    --request POST \
    --header 'Content-Type: text/plain' \
    --data 'CS240 demo order' \
    "$base_url/orders"
