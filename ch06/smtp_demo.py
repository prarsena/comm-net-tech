import smtplib
import socketserver
import threading
from email.message import EmailMessage


MAX_LINE_BYTES = 8192


class SMTPDemoServer(socketserver.TCPServer):
    allow_reuse_address = True


class SMTPDemoHandler(socketserver.StreamRequestHandler):
    def reply(self, text: str) -> None:
        self.wfile.write(f"{text}\r\n".encode("ascii"))
        self.wfile.flush()

    def handle(self) -> None:
        self.reply("220 localhost CS240 SMTP demo")
        message_lines: list[str] = []
        in_data = False

        while raw_line := self.rfile.readline(MAX_LINE_BYTES):
            command = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")

            if in_data:
                if command == ".":
                    self.server.message_lines = message_lines
                    self.reply("250 2.0.0 message stored in local demo")
                    in_data = False
                else:
                    message_lines.append(command[1:] if command.startswith("..") else command)
                continue

            self.server.transcript.append(command)
            upper_command = command.upper()

            if upper_command.startswith("EHLO "):
                self.reply("250-localhost")
                self.reply("250 SIZE 4096")
            elif upper_command.startswith("HELO "):
                self.reply("250 localhost")
            elif upper_command.startswith(("MAIL FROM:", "RCPT TO:")):
                self.reply("250 2.1.0 accepted")
            elif upper_command == "DATA":
                self.reply("354 End data with <CR><LF>.<CR><LF>")
                in_data = True
            elif upper_command in {"NOOP", "RSET"}:
                self.reply("250 2.0.0 OK")
            elif upper_command == "QUIT":
                self.reply("221 2.0.0 goodbye")
                break
            else:
                self.reply("500 5.5.2 command not recognized")


def main() -> None:
    with SMTPDemoServer(("127.0.0.1", 0), SMTPDemoHandler) as server:
        server.transcript = []
        server.message_lines = []
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        message = EmailMessage()
        message["From"] = "student@example.test"
        message["To"] = "instructor@example.test"
        message["Subject"] = "Local SMTP protocol demo"
        message.set_content("This message stays on the local demo server.")

        try:
            with smtplib.SMTP(
                "127.0.0.1",
                server.server_address[1],
                timeout=3,
            ) as client:
                client.send_message(message)
        finally:
            server.shutdown()
            server_thread.join(timeout=3)

        print("SMTP commands exchanged with the loopback-only sink:")
        for command in server.transcript:
            print(f"  C: {command}")

        print("\nMessage captured locally:")
        print("\n".join(server.message_lines))


if __name__ == "__main__":
    main()
