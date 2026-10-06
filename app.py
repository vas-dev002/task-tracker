"""Smoke app for the software factory: a dependency-free HTTP service."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class SmokeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
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
