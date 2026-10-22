"""King Coopa dashboard: serves the static UI and proxies API calls to the door controller.

The proxy avoids CORS (the Flask API sends no CORS headers) and lets info and
controls point at different targets while the dashboard is being built.

Optional coop camera: when KC_GO2RTC_URL is set, the live feed and snapshots are relayed from a
go2rtc instance that is only reachable from here (its API exposes the camera login, so it must
never be published). Only the named streams and these operations are passed through. Audio is
opt-in per connection ("listen"): it uses separate go2rtc streams that transcode the camera's PCMA
to AAC, and the server cuts audio connections off after KC_AUDIO_SECONDS. Live camera connections
are tracked so they can be listed and disconnected from the UI.
Pan/tilt (optional): when KC_CAMERA_HOST, TAPO_USER and TAPO_PASS are set, the dashboard talks
ONVIF to the camera directly (see ptz.py) for small fixed-step moves and presets.
"""
import http.client
import itertools
import json
import os
import re
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from ptz import OnvifPTZ, PTZError, PTZInputError


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
# Open/close/restart go to the controller (default: the same address as info). Reconfigure has its
# own target, defaulting to a fake .invalid host so it can't rewrite the Pi's config until set.
CONTROL_URL = (os.environ.get("KC_CONTROL_URL") or INFO_URL).rstrip("/")
RECONFIGURE_URL = os.environ.get("KC_RECONFIGURE_URL", "http://fake-king-coopa.invalid:8080").rstrip("/")
# Camera relay (optional). go2rtc stream names for each quality the UI offers; the *_audio
# variants add AAC audio (go2rtc runs ffmpeg only while one of them has a viewer).
GO2RTC_URL = os.environ.get("KC_GO2RTC_URL", "").rstrip("/")
CAMERA_STREAMS = {"sd": "coop_sd", "hd": "coop_hd"}
AUDIO_STREAMS = {"sd": "coop_sd_audio", "hd": "coop_hd_audio"}
AUDIO_SECONDS = int(os.environ.get("KC_AUDIO_SECONDS", "300"))
SESSION_ID = re.compile(r"^[a-f0-9]{16,32}$")
# Pan/tilt over ONVIF. Credentials are the camera account, URL-encoded as for go2rtc.
_cam_host = os.environ.get("KC_CAMERA_HOST", "")
_cam_user = urllib.parse.unquote(os.environ.get("TAPO_USER", ""))
_cam_pass = urllib.parse.unquote(os.environ.get("TAPO_PASS", ""))
PTZ = OnvifPTZ(_cam_host, _cam_user, _cam_pass, port=int(os.environ.get("KC_CAMERA_ONVIF_PORT", "2020"))) \
    if _cam_host and _cam_user and _cam_pass else None
# Fixed step sizes in ONVIF's generic -1..1 space; the UI only picks a direction and a size.
PTZ_STEPS = {"small": 0.05, "large": 0.2}
PTZ_DIRS = {"left": (-1, 0), "right": (1, 0), "up": (0, 1), "down": (0, -1)}
for _name, _url in (("KC_INFO_URL", INFO_URL), ("KC_CONTROL_URL", CONTROL_URL),
                    ("KC_RECONFIGURE_URL", RECONFIGURE_URL), ("KC_GO2RTC_URL", GO2RTC_URL)):
    # Only plain HTTP(S) upstreams; urlopen would otherwise also accept file:// and friends.
    if _url and not _url.startswith(("http://", "https://")):
        raise SystemExit(f"{_name} must start with http:// or https:// (got {_url!r}).")
# All interfaces by default: inside a container the published port arrives on eth0, not loopback.
BIND = os.environ.get("BIND", "0.0.0.0")  # nosec B104
PORT = int(os.environ.get("PORT", "8090"))
TIMEOUT = float(os.environ.get("KC_TIMEOUT", "10"))
# The controller's /open and /close only answer once the actuator has finished its stroke and its
# duty-cycle rest (stroke / speed * (1 + duty_cycle), about 30 s with the stock config).
DOOR_TIMEOUT = float(os.environ.get("KC_DOOR_TIMEOUT", "90"))
STARTED = time.time()
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# (method, dashboard path) -> (upstream base, upstream path, timeout)
ROUTES = {
    ("GET", "/api/info"): (INFO_URL, "/info", TIMEOUT),
    ("PUT", "/api/open"): (CONTROL_URL, "/open", DOOR_TIMEOUT),
    ("PUT", "/api/close"): (CONTROL_URL, "/close", DOOR_TIMEOUT),
    ("PUT", "/api/restart"): (CONTROL_URL, "/restart", TIMEOUT),
    ("POST", "/api/reconfigure"): (RECONFIGURE_URL, "/reconfigure", TIMEOUT),
}
MAX_BODY = 64 * 1024


def _agent(ua):
    """Short "Browser on OS" label for the viewers list."""
    browser = next((name for key, name in (("Edg/", "Edge"), ("Firefox/", "Firefox"), ("Chrome/", "Chrome"),
                                           ("Safari/", "Safari")) if key in ua), "Browser")
    system = next((name for key, name in (("Android", "Android"), ("iPhone", "iPhone"), ("iPad", "iPad"),
                                          ("Windows", "Windows"), ("Mac OS", "Mac"), ("Linux", "Linux")) if key in ua),
                  "unknown OS")
    return f"{browser} on {system}"


class CameraSessions:
    """Live camera WebSocket connections, so they can be listed and cut off from the UI.

    A session id (sid) is a random id each page load picks; one tab may reconnect several times.
    Disconnecting a sid closes its sockets and refuses that sid for an hour, so the tab stops
    instead of silently reconnecting; the page then offers a manual reconnect with a new sid.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._ids = itertools.count(1)
        self._live = {}      # conn id -> {"sid", "client", "agent", "quality", "audio", "started", "socks"}
        self._killed = {}    # sid -> time

    def add(self, sid, client, agent, quality, audio, socks):
        with self._lock:
            cid = next(self._ids)
            self._live[cid] = {"sid": sid, "client": client, "agent": agent, "quality": quality,
                               "audio": audio, "started": time.time(), "socks": socks}
            return cid

    def remove(self, cid):
        with self._lock:
            self._live.pop(cid, None)

    def killed(self, sid):
        with self._lock:
            now = time.time()
            for s, t in list(self._killed.items()):
                if now - t > 3600:
                    del self._killed[s]
            return sid in self._killed

    def listing(self):
        with self._lock:
            now = time.time()
            return [{"sid": c["sid"], "client": c["client"], "agent": c["agent"], "quality": c["quality"],
                     "audio": c["audio"], "seconds": int(now - c["started"])} for c in self._live.values()]

    def disconnect(self, sids):
        with self._lock:
            targets = [c for c in self._live.values() if c["sid"] in sids]
            for sid in sids:
                self._killed[sid] = time.time()
        for c in targets:
            _close(c["socks"])
        return len(targets)


def _close(socks):
    for s in socks:
        try:
            s.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass


SESSIONS = CameraSessions()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        # Static files: make browsers revalidate every time (a cheap 304 via Last-Modified) so a
        # redeploy shows up on the next load. API responses set their own no-store in _send.
        if not self.path.startswith("/api/") and self.path != "/status":
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        if url.path.startswith("/api/camera"):
            return self._camera(url)
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
            targets = {"info": INFO_URL, "control": CONTROL_URL, "reconfigure": RECONFIGURE_URL}
            return self._send(200, json.dumps(targets).encode())
        if self.path.startswith("/api/"):
            return self._proxy("GET")
        return super().do_GET()

    def do_PUT(self):
        self._proxy("PUT")

    def do_POST(self):
        if self.path == "/api/camera/ptz":
            return self._ptz_post()
        if self.path == "/api/camera/sessions":
            return self._sessions_post()
        self._proxy("POST")

    def _proxy(self, method):
        route = ROUTES.get((method, self.path))
        if route is None:
            return self._send(404, b'{"error": "unknown route"}')
        base, path, timeout = route

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
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
                self._send(resp.status, resp.read())
        except urllib.error.HTTPError as e:
            self._send(e.code, e.read() or b'{"error": "upstream error"}')
        except TimeoutError:
            # The request reached the controller; it just didn't answer in time. Moves keep going.
            msg = f"no answer within {timeout:.0f}s (the controller may still be working)"
            self._send(504, json.dumps({"error": msg, "target": base}).encode())
        except (OSError, http.client.HTTPException) as e:  # unreachable host, timeout, DNS failure, bad response
            msg = f"upstream unreachable: {getattr(e, 'reason', e)}"
            self._send(502, json.dumps({"error": msg, "target": base}).encode())

    # ---- camera relay ----
    def _camera(self, url):
        if url.path == "/api/camera":
            info = {"enabled": bool(GO2RTC_URL), "qualities": list(CAMERA_STREAMS), "ptz": PTZ is not None,
                    "audio_seconds": AUDIO_SECONDS}
            return self._send(200, json.dumps(info).encode())
        if url.path == "/api/camera/sessions":
            sid = urllib.parse.parse_qs(url.query).get("sid", [""])[0]
            body = {"sessions": SESSIONS.listing(), "killed": bool(sid) and SESSIONS.killed(sid)}
            return self._send(200, json.dumps(body).encode())
        if url.path == "/api/camera/ptz":
            return self._ptz_get()
        if not GO2RTC_URL:
            return self._send(404, b'{"error": "camera not configured"}')
        query = urllib.parse.parse_qs(url.query)
        quality = query.get("q", ["sd"])[0]
        src = CAMERA_STREAMS.get(quality)
        if src is None:
            return self._send(400, b'{"error": "unknown quality"}')
        if url.path == "/api/camera/snapshot":
            return self._camera_snapshot(src)
        if url.path == "/api/camera/ws" and self.headers.get("Upgrade", "").lower() == "websocket":
            sid = query.get("sid", [""])[0]
            if not SESSION_ID.match(sid):
                return self._send(400, b'{"error": "bad session id"}')
            if SESSIONS.killed(sid):
                return self._send(410, b'{"error": "disconnected"}')
            audio = query.get("audio", ["0"])[0] == "1"
            return self._camera_ws(AUDIO_STREAMS[quality] if audio else src, sid, quality, audio)
        return self._send(404, b'{"error": "unknown route"}')

    # ---- pan/tilt ----
    def _ptz_get(self):
        if PTZ is None:
            return self._send(404, b'{"error": "pan/tilt not configured"}')
        try:
            body = {"status": PTZ.status(), "presets": PTZ.presets()}
        except PTZError as e:
            return self._send(502, json.dumps({"error": str(e)}).encode())
        return self._send(200, json.dumps(body).encode())

    def _ptz_post(self):
        """{"action": "move", "dir": "left|right|up|down", "step": "small|large"}
        {"action": "goto", "token": "<preset token>"} | {"action": "save", "name": "<preset name>"}"""
        if PTZ is None:
            return self._send(404, b'{"error": "pan/tilt not configured"}')
        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= 1024:
            return self._send(400, b'{"error": "bad request"}')
        try:
            req = json.loads(self.rfile.read(length))
            action = req.get("action")
        except (ValueError, AttributeError):
            return self._send(400, b'{"error": "bad request"}')
        try:
            if action == "move":
                direction, step = PTZ_DIRS.get(req.get("dir")), PTZ_STEPS.get(req.get("step", "small"))
                if direction is None or step is None:
                    return self._send(400, b'{"error": "unknown direction or step"}')
                PTZ.nudge(direction[0] * step, direction[1] * step)
                result = {"ok": True}
            elif action == "goto":
                PTZ.goto_preset(str(req.get("token", "")))
                result = {"ok": True}
            elif action == "save":
                result = {"ok": True, "token": PTZ.save_preset(str(req.get("name", "")).strip())}
            else:
                return self._send(400, b'{"error": "unknown action"}')
        except PTZInputError as e:
            return self._send(400, json.dumps({"error": str(e)}).encode())
        except PTZError as e:
            return self._send(502, json.dumps({"error": str(e)}).encode())
        return self._send(200, json.dumps(result).encode())

    def _sessions_post(self):
        """{"action": "disconnect", "sid": "<sid>"} | {"action": "disconnect_others", "sid": "<own sid>"}"""
        length = int(self.headers.get("Content-Length") or 0)
        try:
            req = json.loads(self.rfile.read(length)) if 0 < length <= 1024 else {}
            action, sid = req.get("action"), str(req.get("sid", ""))
        except (ValueError, AttributeError):
            action, sid = None, ""
        if not SESSION_ID.match(sid) or action not in ("disconnect", "disconnect_others"):
            return self._send(400, b'{"error": "bad request"}')
        if action == "disconnect":
            sids = {sid}
        else:
            sids = {c["sid"] for c in SESSIONS.listing()} - {sid}
        closed = SESSIONS.disconnect(sids) if sids else 0
        return self._send(200, json.dumps({"ok": True, "closed": closed}).encode())

    def _camera_snapshot(self, src):
        req = urllib.request.Request(f"{GO2RTC_URL}/api/frame.jpeg?src={src}")
        try:
            # Scheme restricted to http(s) at startup.
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # nosec B310
                self._send(200, resp.read(), "image/jpeg")
        except (OSError, http.client.HTTPException):
            self._send(502, b'{"error": "camera unavailable"}')

    def _camera_ws(self, src, sid, quality, audio):
        """Splice the browser's WebSocket to go2rtc's /api/ws for one fixed stream."""
        up = urllib.parse.urlsplit(GO2RTC_URL)
        try:
            upstream = socket.create_connection((up.hostname, up.port or 80), timeout=TIMEOUT)
        except OSError:
            return self._send(502, b'{"error": "camera relay unavailable"}')
        # Replay the handshake with the fixed upstream path. The client's own headers (Host, Origin,
        # Sec-WebSocket-*) are kept as-is so go2rtc's same-origin check sees a matching pair.
        head = [f"GET /api/ws?src={src} HTTP/1.1"] + [f"{k}: {v}" for k, v in self.headers.items()]
        upstream.sendall(("\r\n".join(head) + "\r\n\r\n").encode("latin-1"))
        upstream.settimeout(None)
        self.connection.settimeout(None)

        def pump(src_sock, dst_sock):
            try:
                while data := src_sock.recv(65536):
                    dst_sock.sendall(data)
            except OSError:
                pass
            finally:
                for s in (src_sock, dst_sock):
                    try:
                        s.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass

        socks = (upstream, self.connection)
        cid = SESSIONS.add(sid, self.client_address[0], _agent(self.headers.get("User-Agent", "")),
                           quality, audio, socks)
        # Audio is time-limited on the server too, so a sleeping or forgotten tab can't keep ffmpeg busy.
        cutoff = threading.Timer(AUDIO_SECONDS + 15, _close, args=(socks,)) if audio else None
        if cutoff:
            cutoff.daemon = True
            cutoff.start()
        downstream = threading.Thread(target=pump, args=(upstream, self.connection), daemon=True)
        downstream.start()
        try:
            pump(self.connection, upstream)
            downstream.join()
        finally:
            if cutoff:
                cutoff.cancel()
            SESSIONS.remove(cid)
            upstream.close()
            self.close_connection = True

    def _send(self, status, payload, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    camera = f"  camera -> {GO2RTC_URL}" if GO2RTC_URL else ""
    print(f"King Coopa dashboard on :{PORT}  info -> {INFO_URL}  controls -> {CONTROL_URL}"
          f"  reconfigure -> {RECONFIGURE_URL}{camera}", flush=True)
    ThreadingHTTPServer((BIND, PORT), Handler).serve_forever()
