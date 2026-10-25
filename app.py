"""Smoke app for the software factory: a dependency-free HTTP service."""

import json
import os
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

START_TIME = time.monotonic()


def _utc_now_iso():
    """Current server time as an ISO 8601 UTC timestamp, e.g. 2024-01-01T00:00:00Z."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class SmokeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
        elif self.path == "/status":
            self._send_json(200, {"status": "ok"})
        elif self.path == "/ping":
            self._send_json(200, {"ping": "pong"})
        elif self.path == "/hello":
            self._send_json(200, {"message": "hello"})
        elif self.path == "/ready":
            self._send_json(200, {"ready": True})
        elif self.path == "/live":
            self._send_json(200, {"alive": True})
        elif self.path == "/info":
            self._send_json(200, {"name": "task-tracker", "version": "0.1.0"})
        elif self.path == "/e2e-5605":
            self._send_json(200, {"value": 5605})
        elif self.path == "/e2e-6815":
            self._send_json(200, {"value": 6815})
        elif self.path == "/ui-7910":
            self._send_json(200, {"value": 7910})
        elif self.path == "/ui-4564":
            self._send_json(200, {"value": 4564})
        elif self.path == "/ui-8490":
            self._send_json(200, {"value": 8490})
        elif self.path == "/uptime":
            uptime = max(0.0, time.monotonic() - START_TIME)
            self._send_json(200, {"uptime_seconds": round(uptime, 3)})
        elif self.path == "/time":
            self._send_json(200, {"time": _utc_now_iso()})
        else:
            self._send_json(404, {"error": "not found"})

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), SmokeHandler)
    print(f"listening on :{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
