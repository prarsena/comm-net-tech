#!/usr/bin/env python3
import argparse
from datetime import datetime
import socket


PORT = 17429
MAX_DATAGRAM_BYTES = 2048
MAX_POPUP_CHARS = 512


def display_text(data: bytes) -> str:
    decoded = data.decode("utf-8", errors="replace")
    return "".join(
        character if character.isprintable() else f"\\x{ord(character):02x}"
        for character in decoded
    )


def run_terminal(sock: socket.socket) -> None:
    print(f"Listening for UDP broadcasts on 0.0.0.0:{PORT}. Press Ctrl-C to stop.")
    try:
        while True:
            data, (sender_ip, sender_port) = sock.recvfrom(MAX_DATAGRAM_BYTES)
            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            message = display_text(data)
            print(f"[{timestamp}] from {sender_ip}:{sender_port}: {message}", flush=True)
    except KeyboardInterrupt:
        print("\nListener stopped.")


def run_popup(sock: socket.socket) -> None:
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError as error:
        raise SystemExit(
            "Popup mode requires Tkinter; install your platform's Python Tk package."
        ) from error

    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise SystemExit(f"Could not open a popup window: {error}") from error

    root.title("CS240 Broadcast Message")
    root.geometry("480x180")
    root.resizable(False, False)

    sender_text = tk.StringVar(root, value="Waiting for a message...")
    message_text = tk.StringVar(root, value="")
    ttk.Label(root, textvariable=sender_text).pack(padx=16, pady=(18, 8), anchor="w")
    ttk.Label(
        root,
        textvariable=message_text,
        wraplength=440,
        justify="left",
    ).pack(padx=16, pady=8, anchor="w")
    ttk.Button(root, text="Close", command=root.destroy).pack(
        padx=16,
        pady=(8, 16),
        anchor="e",
    )

    sock.setblocking(False)

    def update_window() -> None:
        for _ in range(20):
            try:
                data, (sender_ip, sender_port) = sock.recvfrom(MAX_DATAGRAM_BYTES)
            except BlockingIOError:
                break

            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            message = display_text(data)
            if len(message) > MAX_POPUP_CHARS:
                message = f"{message[:MAX_POPUP_CHARS]}..."
            sender_text.set(f"From {sender_ip}:{sender_port} at {timestamp}")
            message_text.set(message)

        root.after(100, update_window)

    root.after(100, update_window)
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Receive the CS240 UDP broadcast demo.")
    parser.add_argument(
        "--popup",
        action="store_true",
        help="show the latest message in a small Tkinter window",
    )
    arguments = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("0.0.0.0", PORT))
    except OSError as error:
        sock.close()
        raise SystemExit(f"Could not listen on UDP port {PORT}: {error}") from error

    try:
        if arguments.popup:
            run_popup(sock)
        else:
            run_terminal(sock)
    finally:
        sock.close()


if __name__ == "__main__":
    main()
