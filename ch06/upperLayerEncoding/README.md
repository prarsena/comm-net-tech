# Upper-layer encoding demo

This demo sends a photo from a Python client on macOS to a server on Windows. The client converts a local HEIC image to JPEG; the server can be implemented in Python or Java. Both server implementations use the same network protocol, illustrating that interoperability depends on shared protocols and formats, not on the programming language.

## What the demo shows

- **Format conversion:** the client converts HEIC to JPEG before transmission.
- **TCP:** both programs use a TCP connection on port `8443`. TCP is a byte stream; it does not preserve the boundaries between separate writes.
- **Message framing:** the client sends a 4-byte unsigned, big-endian payload length followed by exactly that many JPEG bytes. The length prefix gives the receiver a message boundary.
- **TLS 1.3:** TLS protects the TCP connection. The servers report the negotiated protocol and cipher suite.
- **Language independence:** the Python client can send the same bytes to either the Python or Java server.

In the course's layered model, the length prefix demonstrates session-style framing and TLS/data-format handling illustrates upper-layer services. In practice, the length prefix is application-level framing over TCP.

> **Demo only:** the Python client disables certificate verification so it can connect to a self-signed demo server. TLS encrypts the connection, but this client does not authenticate the server. Do not use this configuration for sensitive data.

## Project layout

```text
upperLayerEncoding/
├── README.md
├── java-server.md               # Java server architecture notes
├── client/
│   ├── client.py                # HEIC-to-JPEG client
│   └── requirements.txt
└── server/
    ├── java/
    │   └── PhotoServer.java     # Java TLS/TCP server
    └── python/
        ├── server.py            # Python alternative server
        └── requirements.txt
```

Local-only files are intentionally not tracked: component virtual environments (`.venv`), the sample `client/IMG_0806.HEIC`, generated TLS credentials (`server/python/cert.pem` and `key.pem`), the Java PKCS#12 keystore, and received JPEGs. The old project-root Windows virtual environment has been removed. Create a fresh `.venv` in the component you run on each machine rather than copying environments between macOS and Windows.

## macOS: prepare and run the client

From `upperLayerEncoding/client`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python client.py <WINDOWS_IP> /path/to/photo.HEIC
```

Use the Windows host's LAN IP address. If you have the local sample image, you can pass `IMG_0806.HEIC` instead of `/path/to/photo.HEIC`.

## Windows: run the Java server

Use a JDK 11 or later. From `upperLayerEncoding/server/java`, create a local PKCS#12 keystore. `keytool` will prompt for a keystore password; use at least six characters and remember it for the next step.

```powershell
keytool -genkeypair -alias photoserver -keyalg RSA -keysize 2048 `
  -validity 365 -storetype PKCS12 -keystore keystore.p12 `
  -dname "CN=photo-server"
```

Then set the password chosen above, compile, and start the server in the same PowerShell window:

```powershell
$env:PHOTO_KEYSTORE_PASSWORD = "<keystore password>"
javac PhotoServer.java
java PhotoServer
```

The server listens on TCP port `8443` and saves the received JPEG as `received_from_python.jpg` in `server/java`. Allow inbound TCP `8443` through Windows Firewall on the private network if the client cannot connect.

If you prefer to reuse the Python server's PEM pair, create `keystore.p12` from `server/java` with OpenSSL:

```powershell
openssl pkcs12 -export -in ..\python\cert.pem -inkey ..\python\key.pem `
  -out keystore.p12 -name photoserver
```

If the PEM files do not exist yet, start the Python server once to generate them, then stop it with `Ctrl+C` before starting Java. Set `PHOTO_KEYSTORE_PASSWORD` to the export password when starting the Java server.

## Optional: run the Python server

From `upperLayerEncoding/server/python` on Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python server.py
```

The Python server generates a local self-signed `cert.pem` and `key.pem` on first run if they are missing, then listens on the same TCP port. It can be used instead of the Java server; only one server can listen on port `8443` at a time.

See [`java-server.md`](java-server.md) for the Java server's protocol architecture.
