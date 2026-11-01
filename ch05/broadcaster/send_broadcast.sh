#!/usr/bin/env bash
set -euo pipefail

PORT=17429
DEFAULT_MESSAGE="Hello from the CS240 UDP broadcast demo"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if (( $# > 2 )); then
    printf 'Usage: bash code/ch05/broadcaster/send_broadcast.sh ["message"] [interface]\n' >&2
    exit 2
fi

message="${1:-$DEFAULT_MESSAGE}"
interface="${2:-}"

if [[ -z "$message" || "$message" == *$'\n'* || "$message" == *$'\r'* ]]; then
    printf 'Message must be non-empty and contain no newline characters.\n' >&2
    exit 2
fi

message_bytes="$(printf '%s' "$message" | LC_ALL=C wc -c | tr -d '[:space:]')"
if (( message_bytes > 256 )); then
    printf 'Message is %s bytes; the limit is 256 bytes.\n' "$message_bytes" >&2
    exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
    printf 'This demo requires python3.\n' >&2
    exit 127
fi
if ! command -v socat >/dev/null 2>&1; then
    printf 'This demo requires socat. Install it with your platform package manager.\n' >&2
    exit 127
fi

if [[ -n "$interface" ]]; then
    network_report="$(python3 "$SCRIPT_DIR/network_info.py" --interface "$interface")"
else
    network_report="$(python3 "$SCRIPT_DIR/network_info.py")"
fi
broadcast_address="$(
    printf '%s\n' "$network_report" |
        sed -n 's/^Broadcast address: *//p'
)"

if [[ -z "$broadcast_address" || "$broadcast_address" == "unavailable" ]]; then
    printf '%s\n' "$network_report"
    printf 'No usable IPv4 broadcast address was found; nothing was sent.\n' >&2
    exit 1
fi

printf '%s\n' "$network_report"
printf '\nThis sends one %s-byte UDP datagram to every device on this broadcast subnet.\n' "$message_bytes"
if [[ ! -t 0 ]]; then
    printf 'Refusing to send without interactive confirmation.\n' >&2
    exit 2
fi

read -r -p "Send to ${broadcast_address}:${PORT}? [y/N] " confirmation
case "$confirmation" in
    y | Y | yes | YES | Yes) ;;
    *)
        printf 'Canceled; nothing was sent.\n'
        exit 0
        ;;
esac

printf 'Sending one UDP datagram to %s:%s.\n' "$broadcast_address" "$PORT"
printf '%s' "$message" |
    socat -u - "UDP4-DATAGRAM:${broadcast_address}:${PORT},broadcast"
