# Chapter 6 Code Demos

Small examples for exploring application protocols and data formats. Run commands
from the course workspace root unless noted. No third-party Python packages are needed.

| Demo | Run | What it shows |
|---|---|---|
| JSON representation | `python3 code/ch06/represent_data.py` | Encode structured data as UTF-8 JSON, then decode it |
| Local HTTP server | `python3 code/ch06/http_demo.py` | A loopback-only HTTP service with GET and POST routes |
| HTTP client | `bash code/ch06/http_client.sh` | Use `curl` to inspect HTTP requests, headers, status, and body |
| DNS records | `bash code/ch06/dns_lookup.sh [domain]` | Use `dig` to query A, AAAA, MX, and NS records |
| SMTP exchange | `python3 code/ch06/smtp_demo.py` | Send a sample message to a local SMTP sink and inspect commands |
| TLS certificate | `python3 code/ch06/tls_inspect.py` | Verify a TLS connection and display its version, cipher, and certificate |

## HTTP exercise

1. Start `http_demo.py` in one terminal.
2. In another terminal, run `http_client.sh` or use the `curl` commands in the
   Chapter 6 Part 2 slides.
3. Stop the server with Ctrl-C.

The HTTP server and SMTP sink bind only to `127.0.0.1`. The SMTP example does not
send email outside the computer. DNS queries use the system-configured resolver.
The TLS example makes one verified connection to `example.com` on port 443; it does
not send credentials or disable certificate checks.

`dig` and `curl` must be installed for their shell demos. The TLS demo needs network
access. Output can vary with DNS, certificates, and network conditions.
