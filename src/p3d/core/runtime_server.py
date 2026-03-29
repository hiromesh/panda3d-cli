"""JSON-RPC 2.0 server — runs as a Panda3D task inside the game process."""

from __future__ import annotations

import json
import os
import selectors
import socket
import struct
from pathlib import Path
from typing import Any, Callable

from direct.task.Task import Task


class ControlServer:

    def __init__(self, sock_path: str | Path, base: Any):
        self.sock_path = Path(sock_path)
        self.base = base
        self.methods: dict[str, Callable] = {}
        self.sel = selectors.DefaultSelector()
        self.server_sock: socket.socket | None = None
        self._clients: list[socket.socket] = []
        self._buffers: dict[int, bytes] = {}

        self.register("ping", lambda params: {"pong": True})
        self.register("shutdown", self._handle_shutdown)
        self.register("status", self._handle_status)

    def _handle_shutdown(self, params: dict) -> dict:
        self.base.taskMgr.doMethodLater(0.1, lambda task: self.base.userExit(), "shutdown")
        return {"ok": True}

    def _handle_status(self, params: dict) -> dict:
        result: dict[str, Any] = {"running": True, "pid": os.getpid()}
        try:
            result["fps"] = round(self.base.graphicsEngine.getFrameRate(), 1)
        except Exception:
            result["fps"] = 0
        try:
            result["node_count"] = len(self.base.render.findAllMatches("**"))
        except Exception:
            result["node_count"] = 0
        return result

    def register(self, method: str, handler: Callable) -> None:
        self.methods[method] = handler

    def start(self) -> None:
        if self.sock_path.exists():
            self.sock_path.unlink()
        self.server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_sock.bind(str(self.sock_path))
        self.server_sock.listen(5)
        self.server_sock.setblocking(False)
        self.sel.register(self.server_sock, selectors.EVENT_READ, data="accept")
        self.base.taskMgr.add(self._poll_task, "p3d-control-server")

    def stop(self) -> None:
        for client in self._clients:
            try:
                client.close()
            except OSError:
                pass
        self._clients.clear()
        self._buffers.clear()
        if self.server_sock:
            self.sel.unregister(self.server_sock)
            self.server_sock.close()
            self.server_sock = None
        if self.sock_path.exists():
            self.sock_path.unlink()

    def _poll_task(self, task: Any) -> int:
        for key, _ in self.sel.select(timeout=0):
            if key.data == "accept":
                self._accept()
            else:
                self._handle_client(key.fileobj)
        return Task.cont

    def _accept(self) -> None:
        conn, _ = self.server_sock.accept()
        conn.setblocking(False)
        self._clients.append(conn)
        self._buffers[id(conn)] = b""
        self.sel.register(conn, selectors.EVENT_READ, data="client")

    def _handle_client(self, conn: socket.socket) -> None:
        try:
            data = conn.recv(65536)
            if not data:
                self._remove_client(conn)
                return

            buf_key = id(conn)
            self._buffers[buf_key] = self._buffers.get(buf_key, b"") + data

            while True:
                buf = self._buffers[buf_key]
                if len(buf) < 4:
                    break
                msg_len = struct.unpack("!I", buf[:4])[0]
                if len(buf) < 4 + msg_len:
                    break
                msg_bytes = buf[4:4 + msg_len]
                self._buffers[buf_key] = buf[4 + msg_len:]

                response = self._dispatch(msg_bytes)
                resp_bytes = json.dumps(response).encode("utf-8")
                conn.sendall(struct.pack("!I", len(resp_bytes)) + resp_bytes)

        except (ConnectionResetError, BrokenPipeError, OSError):
            self._remove_client(conn)

    def _remove_client(self, conn: socket.socket) -> None:
        try:
            self.sel.unregister(conn)
        except (KeyError, ValueError):
            pass
        try:
            conn.close()
        except OSError:
            pass
        if conn in self._clients:
            self._clients.remove(conn)
        self._buffers.pop(id(conn), None)

    def _dispatch(self, msg_bytes: bytes) -> dict:
        try:
            request = json.loads(msg_bytes)
        except json.JSONDecodeError:
            return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}

        method = request.get("method")
        params = request.get("params", {})
        req_id = request.get("id")

        if method not in self.methods:
            return {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {method}"}, "id": req_id}

        try:
            result = self.methods[method](params)
            return {"jsonrpc": "2.0", "result": result, "id": req_id}
        except Exception as e:
            return {"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}, "id": req_id}
