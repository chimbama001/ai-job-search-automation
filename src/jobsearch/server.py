"""Local dashboard: a stdlib HTTP server bound to localhost only."""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files

from .storage import Store

STATUS_PATH = re.compile(r"^/api/jobs/([a-z0-9-]{1,80})$")
MAX_BODY = 1024


def make_handler(store: Store):
    page = files("jobsearch").joinpath("dashboard/index.html").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'self' 'unsafe-inline' "
                "https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
                "script-src 'self' 'unsafe-inline'",
            )
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj) -> None:
            self._send(code, json.dumps(obj).encode())

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, page, "text/html; charset=utf-8")
            elif self.path == "/api/jobs":
                self._json(200, store.all())
            else:
                self._json(404, {"error": "not found"})

        def do_PATCH(self):
            m = STATUS_PATH.match(self.path)
            length = int(self.headers.get("Content-Length") or 0)
            if not m or length > MAX_BODY:
                return self._json(400, {"error": "bad request"})
            try:
                status = json.loads(self.rfile.read(length) or b"{}").get("status", "")
                ok = store.set_status(m.group(1), status)
            except (ValueError, AttributeError) as exc:
                return self._json(400, {"error": str(exc)})
            self._json(200 if ok else 404, {"ok": ok})

        def log_message(self, fmt, *args):  # quieter console
            pass

    return Handler


def serve(store: Store, port: int = 8765) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(store))
    print(f"Dashboard running at http://127.0.0.1:{port}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
