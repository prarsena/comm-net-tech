#!/usr/bin/env python3
import http.server
import socketserver
import urllib.parse
from datetime import datetime

PORT = 9999
MESSAGES = []

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>Subnet Message Wall</title>
    <meta http-equiv="refresh" content="2">
    <style>
        body {{ font-family: monospace; background: #121212; color: #00ff66; padding: 20px; }}
        h1 {{ border-bottom: 2px solid #00ff66; padding-bottom: 10px; }}
        .msg {{ background: #1e1e1e; border-left: 4px solid #00ff66; margin: 10px 0; padding: 10px; }}
        .time {{ color: #888; font-size: 0.85em; }}
        .sender {{ color: #00bfff; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>[Live Subnet Feed - Port {port}]</h1>
    <p>Send a message: <code>curl -X POST -d "Your Name: Hello" http://&lt;IP&gt;:{port}/</code></p>
    <hr/>
    <div id="messages">
        {content}
    </div>
</body>
</html>
"""

class MessageWallHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        
        if not MESSAGES:
            formatted_msgs = "<div class='msg'>No messages yet. Waiting for traffic...</div>"
        else:
            items = []
            for t, ip, txt in reversed(MESSAGES):
                items.append(f"<div class='msg'><span class='time'>[{t}]</span> <span class='sender'>{ip}</span>: {txt}</div>")
            formatted_msgs = "\n".join(items)
            
        html = HTML_TEMPLATE.format(port=PORT, content=formatted_msgs)
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8", errors="replace")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        client_ip = self.client_address[0]
        MESSAGES.append((timestamp, client_ip, body))
        print(f"[RECV] From {client_ip} at {timestamp}: {body}")
        
        # Return 201 Created to the client
        self.send_response(201)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"Message received: '{body}'\n".encode("utf-8"))

    # Suppress standard noisy access logs
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), MessageWallHandler) as httpd:
        print(f"[*] Server running on all interfaces at port {PORT}")
        print(f"[*] Open http://localhost:{PORT} in your browser")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
