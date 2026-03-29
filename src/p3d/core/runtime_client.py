"""JSON-RPC 2.0 client — connects to the game's control server via Unix socket."""

from __future__ import annotations

import json
import socket
import struct
from pathlib import Path
from typing import Any


class RuntimeClient:

    def __init__(self, sock_path: str | Path, timeout: float = 5.0):
        self.sock_path = Path(sock_path)
        self.timeout = timeout
        self._id_counter = 0

    def call(self, method: str, params: dict | None = None) -> Any:
        self._id_counter += 1
        request = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": self._id_counter}

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(str(self.sock_path))
        try:
            msg = json.dumps(request).encode("utf-8")
            sock.sendall(struct.pack("!I", len(msg)) + msg)

            header = _recv_exact(sock, 4)
            resp_bytes = _recv_exact(sock, struct.unpack("!I", header)[0])
            response = json.loads(resp_bytes)

            if "error" in response:
                err = response["error"]
                raise RuntimeError(f"RPC error ({err.get('code', '?')}): {err.get('message', 'unknown')}")
            return response.get("result")
        finally:
            sock.close()

    def is_connected(self) -> bool:
        try:
            self.call("ping")
            return True
        except Exception:
            return False

    def shutdown(self) -> dict:
        return self.call("shutdown")

    def status(self) -> dict:
        return self.call("status")


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed while reading response")
        buf += chunk
    return buf
