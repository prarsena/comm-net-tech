import socket
import datetime

HOST = "0.0.0.0"
PORT = 9999


def now():
    return datetime.datetime.now().strftime("%H:%M:%S")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))

    print(f"📟 SkyTel-Style Pager Dispatch Center -- listening on UDP port {PORT}")
    print("   No connection setup. No handshake. Pages just show up.")
    print("   Press Ctrl+C to shut down the dispatch center.\n")

    try:
        while True:
            data, sender_addr = sock.recvfrom(1024)
            sender_ip, sender_port = sender_addr
            message = data.decode("utf-8", errors="replace")
            print(f'[{now()}] 📟 PAGE from {sender_ip}:{sender_port} -> "{message}"')

            # App-level reply only -- UDP itself has no idea this datagram
            # is "related" to the page that triggered it. No handshake, no ACK.
            reply = f"MSG RECEIVED -- {now()}".encode("utf-8")
            sock.sendto(reply, sender_addr)
    except KeyboardInterrupt:
        print("\n📟 Dispatch center shutting down.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
