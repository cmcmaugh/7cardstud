from __future__ import annotations

import http.server
import socket
import socketserver
import sys
import threading
import time
import webbrowser


def main() -> None:
    port = _free_port()
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), handler) as server:
        url = f"http://127.0.0.1:{port}/pyodide/"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(f"In-browser 7-card stud is running at {url}")
        print("Close this window or press Ctrl+C to stop the static server.")
        time.sleep(0.4)
        webbrowser.open(url)
        try:
            while thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            server.shutdown()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


if __name__ == "__main__":
    sys.exit(main())
