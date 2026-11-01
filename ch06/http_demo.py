from http.server import BaseHTTPRequestHandler, HTTPServer


MAX_BODY_BYTES = 4096


class DemoHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def reply(self, status: int, text: str) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self.reply(200, f"GET {self.path}\n")

    def do_POST(self) -> None:
        content_length = self.headers.get("Content-Length")
        if content_length is None or not content_length.isdecimal():
            self.reply(400, "Invalid Content-Length\n")
            return

        length = int(content_length)
        if length > MAX_BODY_BYTES:
            self.reply(413, "Request body too large\n")
            return

        body = self.rfile.read(length)
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            self.reply(400, "Request body must be UTF-8\n")
            return

        self.reply(200, f"POST received: {text}\n")


if __name__ == "__main__":
    print("Listening only on 127.0.0.1:8000. Press Ctrl-C to stop.")
    HTTPServer(("127.0.0.1", 8000), DemoHandler).serve_forever()
