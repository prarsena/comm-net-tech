import io
import os
import socket
import ssl
import sys
from PIL import Image
import pillow_heif

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()


def convert_and_compress(heic_path, quality=80):
    """Layer 6 Transformation: HEIC -> Compressed JPEG in memory"""
    print(f"\n--- Layer 6: Presentation (Data Format & Compression) ---")
    orig_size = os.path.getsize(heic_path)
    print(f"[*] Original Source: {heic_path} ({orig_size:,} bytes)")

    # Open HEIC and convert to RGB
    img = Image.open(heic_path)

    # Compress into an in-memory byte buffer as JPEG
    jpeg_buffer = io.BytesIO()
    img.save(jpeg_buffer, format="JPEG", quality=quality, optimize=True)
    jpeg_bytes = jpeg_buffer.getvalue()

    compressed_size = len(jpeg_bytes)
    ratio = (1 - (compressed_size / orig_size)) * 100
    print(f"[*] Converted & Compressed to JPEG ({quality}% quality)")
    print(f"[*] Compressed wire payload size: {compressed_size:,} bytes")
    print(f"[*] Bandwidth saved: {ratio:.1f}%")

    return jpeg_bytes

def main():
    if len(sys.argv) < 3:
        print("Usage: python client.py <server_ip> <path_to_image.heic>")
        sys.exit(1)

    server_ip = sys.argv[1]
    heic_file = sys.argv[2]
    port = 8443

    # 1. Transform data (Layer 6: Compression & Format)
    jpeg_payload = convert_and_compress(heic_file, quality=80)

    # 2. Setup TLS Context (Layer 6: Encryption)
    tls_context = ssl.create_default_context()
    tls_context.check_hostname = False
    tls_context.verify_mode = ssl.CERT_NONE

    print(f"\n--- Layer 4 & 5: Transport & Session ---")
    print(f"[*] Dialing raw TCP socket to {server_ip}:{port}...")

    # Step A: Layer 4 Transport connection FIRST
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.connect((server_ip, port))
    print(f"[+] Layer 4 TCP connection established!")

    # Step B: Layer 6/5 Wrap active socket with TLS
    with tls_context.wrap_socket(
        raw_socket, server_hostname=server_ip
    ) as tls_socket:
        print(f"[+] Layer 6 TLS Handshake Complete!")
        print(f"[+] Cipher Suite: {tls_socket.cipher()}")
        print(f"[+] TLS Protocol: {tls_socket.version()}")

        # 3. Transmit Payload
        print(f"\n--- Transmitting Payload ---")
        length_prefix = len(jpeg_payload).to_bytes(4, byteorder="big")
        tls_socket.sendall(length_prefix)
        tls_socket.sendall(jpeg_payload)
        print(f"[+] Sent {len(jpeg_payload):,} encrypted JPEG bytes to server.")

        # Graceful Layer 5/TLS teardown
        try:
            tls_socket.unwrap()
        except Exception:
            pass

    print("[*] Transfer complete. Socket closed.")




if __name__ == "__main__":
    main()
