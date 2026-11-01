#!/usr/bin/env bash
set -euo pipefail

domain="${1:-example.com}"

if [[ ! "$domain" =~ ^[[:alnum:]][[:alnum:]._-]*$ ]]; then
    printf 'Usage: bash code/ch06/dns_lookup.sh [domain]\n' >&2
    printf 'Use a DNS name containing only letters, digits, dots, hyphens, or underscores.\n' >&2
    exit 2
fi

if ! command -v dig >/dev/null 2>&1; then
    printf 'This demo requires dig (usually included with BIND utilities).\n' >&2
    exit 127
fi

printf 'DNS answers for %s using the system-configured resolver\n' "$domain"
for record_type in A AAAA MX NS; do
    printf '\n%s records:\n' "$record_type"
    dig "$domain" "$record_type" +noall +answer
done
