from __future__ import annotations

import socket
import sys
import threading
import time
import webbrowser

from stud_sim.http_server import build_server


def main() -> None:
    host = "127.0.0.1"
    port = _free_port()
    server = build_server(host, port)
    url = f"http://{host}:{port}"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"7-card stud is running at {url}")
    print("Close this window or press Ctrl+C to stop the game.")
    time.sleep(0.4)
    webbrowser.open(url)

    try:
        while thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


if __name__ == "__main__":
    sys.exit(main())
