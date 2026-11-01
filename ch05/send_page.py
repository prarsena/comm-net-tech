import socket
import sys

PORT = 9999


def main():
    if len(sys.argv) < 3:
        print('Usage: python3 send_page.py <server_ip> "<message>"')
        print('Example: python3 send_page.py 192.168.1.42 "Meet at the food court @ noon"')
        sys.exit(1)

    server_ip = sys.argv[1]
    message = sys.argv[2]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)

    print(f'📟 Sending page to {server_ip}:{PORT} -> "{message}"')
    sock.sendto(message.encode("utf-8"), (server_ip, PORT))

    try:
        reply, _ = sock.recvfrom(1024)
        print(f"📟 Reply: {reply.decode('utf-8', errors='replace')}")
    except socket.timeout:
        # No retry, no error -- UDP never promised a reply in the first place.
        print("📟 No reply received (timed out) -- and that's OK, UDP never promised one.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
