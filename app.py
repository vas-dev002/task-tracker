"""Smoke app for the software factory: a dependency-free HTTP service."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


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
