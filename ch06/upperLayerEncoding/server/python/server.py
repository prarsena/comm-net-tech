import datetime
import os
import ssl
import socket
import subprocess
import sys
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

SERVER_DIR = Path(__file__).resolve().parent
CERT_FILE = SERVER_DIR / "cert.pem"
KEY_FILE = SERVER_DIR / "key.pem"
OUTPUT_FILE = SERVER_DIR / "received_upload.jpg"


def ensure_cert():
    """Generates self-signed TLS cert and private key using pure Python."""
    if CERT_FILE.exists() and KEY_FILE.exists():
        return

    print("[*] Generating self-signed TLS certificate (cert.pem, key.pem)...")

    # Generate 2048-bit RSA private key
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Self-sign certificate details
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "photo-server"),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=1)
        )
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(days=7)
        )
        .sign(key, hashes.SHA256())
    )

    # Write private key
    with KEY_FILE.open("wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Write certificate
    with CERT_FILE.open("wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print("[+] Created cert.pem and key.pem successfully.")


def receive_exact(conn, size):
    """Read exactly size bytes from a TCP stream or report an early disconnect."""
    data = bytearray()
    while len(data) < size:
        chunk = conn.recv(size - len(data))
        if not chunk:
            raise EOFError(f"Connection closed after {len(data)} of {size} bytes.")
        data.extend(chunk)
    return bytes(data)


def main():
    ensure_cert()
    HOST = "0.0.0.0"
    PORT = 8443

    # 1. Setup Layer 6 (TLS Presentation Security)
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3
    context.load_cert_chain(certfile=str(CERT_FILE), keyfile=str(KEY_FILE))

    # 2. Setup Layer 4 (Transport / TCP Socket)
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    raw_socket.bind((HOST, PORT))
    raw_socket.listen(1)

    print(f"[*] Photo Ingestion Server listening on port {PORT}...")
    print("[*] Waiting for client connection over TLS...")

    # Wrap the raw socket in TLS
    with context.wrap_socket(raw_socket, server_side=True) as tls_socket:
        conn, addr = tls_socket.accept()
        print(f"\n[+] Layer 5/4 Session established with: {addr}")
        print(f"[+] Layer 6 TLS Protocol negotiated: {conn.version()}")
        print(f"[+] Layer 6 TLS Cipher negotiated: {conn.cipher()}")

        # TCP is a byte stream, so read the full length prefix explicitly.
        raw_size = receive_exact(conn, 4)
        total_bytes = int.from_bytes(raw_size, byteorder="big")
        if total_bytes == 0:
            raise ValueError("The JPEG payload length must be greater than zero.")
        print(f"[+] Expecting {total_bytes:,} bytes of JPEG data...")

        # TLS decrypts application data; TCP may return the payload in partial reads.
        received_data = bytearray()
        while len(received_data) < total_bytes:
            remaining = total_bytes - len(received_data)
            chunk = conn.recv(min(16384, remaining))
            if not chunk:
                raise EOFError(
                    f"Connection closed early at {len(received_data):,} "
                    f"of {total_bytes:,} bytes."
                )
            received_data.extend(chunk)
            # Print live progress bar
            pct = (len(received_data) / total_bytes) * 100
            print(
                f"\r[+] Received {len(received_data):,} / {total_bytes:,} bytes ({pct:.1f}%)",
                end="",
                flush=True,
            )

        print()  # newline after progress bar


        # Save received file
        output_file = OUTPUT_FILE
        with output_file.open("wb") as f:
            f.write(received_data)

        print(f"[+] Successfully received and decrypted: {output_file}")
        print(f"[+] Total payload on disk: {os.path.getsize(output_file):,} bytes")

        # Open the image automatically using native OS viewer
        if sys.platform == "darwin":
            subprocess.run(["open", str(output_file)])
        elif sys.platform == "win32":
            os.startfile(str(output_file))
        else:
            subprocess.run(["xdg-open", str(output_file)])


if __name__ == "__main__":
    main()
