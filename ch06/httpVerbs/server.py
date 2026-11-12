# server.py
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

# In-memory "database" to demonstrate state change and idempotency
RESOURCES = {
    1: {"id": 1, "name": "Alice", "role": "Student"}
}

class DemoHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))  # L5 Framing
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/users":
            self._send_json(200, list(RESOURCES.values()))
        else:
            self._send_json(404, {"error": "Not Found"})

    def do_POST(self):
        if self.path == "/api/users":
            length = int(self.headers.get('Content-Length', 0))
            raw_data = self.rfile.read(length)
            payload = json.loads(raw_data.decode('utf-8'))
            
            new_id = max(RESOURCES.keys(), default=0) + 1
            payload["id"] = new_id
            RESOURCES[new_id] = payload
            self._send_json(201, payload)
        else:
            self._send_json(404, {"error": "Not Found"})

    def do_PUT(self):
        # Example: PUT /api/users/1
        if self.path.startswith("/api/users/"):
            user_id = int(self.path.split("/")[-1])
            length = int(self.headers.get('Content-Length', 0))
            raw_data = self.rfile.read(length)
            payload = json.loads(raw_data.decode('utf-8'))
            
            payload["id"] = user_id
            RESOURCES[user_id] = payload  # Idempotent overwrite
            self._send_json(200, payload)
        else:
            self._send_json(404, {"error": "Not Found"})

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), DemoHandler)
    print("Serving HTTP demo on http://127.0.0.1:8000 (Ctrl+C to quit)...")
    server.serve_forever()