#!/usr/bin/env python3
import http.server
import socketserver
import sys

PORT = 80

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Prevent browser caching so student edits show up immediately
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

def run():
    # Allow immediate port reuse right after Ctrl+C
    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer(("", PORT), NoCacheHTTPRequestHandler) as httpd:
            print(f"[*] Serving index.html on http://0.0.0.0:{PORT}")
            print("[*] Press Ctrl+C to stop the server.")
            httpd.serve_forever()
    except PermissionError:
        sys.exit(f"[!] Permission denied on port {PORT}. Run with: sudo python3 server.py")
    except KeyboardInterrupt:
        print("\n[*] Server stopped cleanly.")

if __name__ == "__main__":
    run()