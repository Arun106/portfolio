import socket
from unittest.mock import patch, MagicMock
from common import run_cases

def check(data):
    reachable, latency_ms = data
    connection = MagicMock()
    connection.__enter__.return_value = connection
    effect = None if reachable else socket.timeout("No response")
    with patch("socket.create_connection", return_value=connection,
               side_effect=effect):
        with socket.create_connection(("127.0.0.1", 9000), timeout=0.1):
            assert latency_ms <= 100, f"Latency {latency_ms} ms"
    connection.__exit__.assert_called_once()

if __name__ == "__main__":
    raise SystemExit(run_cases("tc24_network", [
        ("reachable", (True, 30), None),
        ("slow", (True, 130), AssertionError),
        ("unreachable", (False, 0), socket.timeout),
    ], check))
