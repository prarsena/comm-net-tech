#!/usr/bin/env python
from __future__ import print_function
import sys

try:
    # Python 3
    import http.server as SimpleHTTPServer
    import socketserver as SocketServer
except ImportError:
    # Python 2 fallback
    import SimpleHTTPServer
    import SocketServer

PORT = 80


class NoCacheHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Prevent browser caching so student edits show up immediately
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)


def run():
    # Allow immediate port reuse right after Ctrl+C
    SocketServer.TCPServer.allow_reuse_address = True

    try:
        httpd = SocketServer.TCPServer(("", PORT), NoCacheHTTPRequestHandler)
    except Exception as exc:
        if getattr(exc, "errno", None) == 13:
            sys.exit("[!] Permission denied on port {0}. Run with: sudo python server.py".format(PORT))
        raise

    print("[*] Serving index.html on http://0.0.0.0:{0}".format(PORT))
    print("[*] Press Ctrl+C to stop the server.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped cleanly.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run()