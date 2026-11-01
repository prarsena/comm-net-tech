import socket
import ssl


HOST = "example.com"
PORT = 443

context = ssl.create_default_context()
with socket.create_connection((HOST, PORT), timeout=5) as raw_socket:
    with context.wrap_socket(raw_socket, server_hostname=HOST) as connection:
        certificate = connection.getpeercert()
        cipher = connection.cipher()

        print("Host:", HOST)
        print("TLS version:", connection.version())
        print("Cipher:", cipher[0] if cipher else "unknown")
        print("Certificate subject:", certificate.get("subject"))
        print("Certificate issuer:", certificate.get("issuer"))
