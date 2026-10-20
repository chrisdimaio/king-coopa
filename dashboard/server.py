"""King Coopa dashboard: serves the static UI and proxies API calls to the door controller.

The proxy avoids CORS (the Flask API sends no CORS headers) and lets info and
controls point at different targets while the dashboard is being built.
"""
import http.client
import json
import os
import time
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


def _load_dotenv(path):
    """Minimal KEY=VALUE loader for a local, gitignored .env. Real env vars win."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

INFO_URL = os.environ.get("KC_INFO_URL", "").rstrip("/")
if not INFO_URL:
    raise SystemExit("KC_INFO_URL is not set (e.g. http://<pi-address>:8080). See dashboard/.env.example.")
CONTROL_URL = os.environ.get("KC_CONTROL_URL", "http://fake-king-coopa.invalid:8080").rstrip("/")
# Only plain HTTP(S) upstreams; urlopen would otherwise also accept file:// and friends.
for _name, _url in (("KC_INFO_URL", INFO_URL), ("KC_CONTROL_URL", CONTROL_URL)):
    if not _url.startswith(("http://", "https://")):
        raise SystemExit(f"{_name} must start with http:// or https:// (got {_url!r}).")
# All interfaces by default: inside a container the published port arrives on eth0, not loopback.
BIND = os.environ.get("BIND", "0.0.0.0")  # nosec B104
PORT = int(os.environ.get("PORT", "8090"))
TIMEOUT = float(os.environ.get("KC_TIMEOUT", "10"))
STARTED = time.time()
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# (method, dashboard path) -> (upstream base, upstream path)
ROUTES = {
    ("GET", "/api/info"): (INFO_URL, "/info"),
    ("PUT", "/api/open"): (CONTROL_URL, "/open"),
    ("PUT", "/api/close"): (CONTROL_URL, "/close"),
    ("PUT", "/api/restart"): (CONTROL_URL, "/restart"),
    ("POST", "/api/reconfigure"): (CONTROL_URL, "/reconfigure"),
}
MAX_BODY = 64 * 1024


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/status":
            # Health of the dashboard itself, for Homepage / Uptime Kuma. Never contacts King Coopa,
            # so a Pi outage doesn't make the dashboard look down.
            return self._send(200, json.dumps({
                "status": "ok",
                "service": "king-coopa-dashboard",
                "uptime_seconds": int(time.time() - STARTED),
                "started": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(STARTED)),
            }).encode())
        if self.path == "/api/targets":
            return self._send(200, json.dumps({"info": INFO_URL, "control": CONTROL_URL}).encode())
        if self.path.startswith("/api/"):
            return self._proxy("GET")
        return super().do_GET()

    def do_PUT(self):
        self._proxy("PUT")

    def do_POST(self):
        self._proxy("POST")

    def _proxy(self, method):
        route = ROUTES.get((method, self.path))
        if route is None:
            return self._send(404, b'{"error": "unknown route"}')
        base, path = route

        body = None
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            return self._send(413, b'{"error": "body too large"}')
        if length:
            body = self.rfile.read(length)

        req = urllib.request.Request(base + path, data=body, method=method)
        if body is not None:
            req.add_header("Content-Type", self.headers.get("Content-Type", "text/yaml"))
        try:
            # Upstream scheme is restricted to http(s) at startup.
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # nosec B310
                self._send(resp.status, resp.read())
        except urllib.error.HTTPError as e:
            self._send(e.code, e.read() or b'{"error": "upstream error"}')
        except (OSError, http.client.HTTPException) as e:  # unreachable host, timeout, DNS failure, bad response
            msg = f"upstream unreachable: {getattr(e, 'reason', e)}"
            self._send(502, json.dumps({"error": msg, "target": base}).encode())

    def _send(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    print(f"King Coopa dashboard on :{PORT}  info -> {INFO_URL}  controls -> {CONTROL_URL}", flush=True)
    ThreadingHTTPServer((BIND, PORT), Handler).serve_forever()
