"""Minimal ONVIF pan/tilt client for the coop camera (standard library only).

Only the handful of PTZ operations the dashboard needs: status, small relative moves,
and presets. Every move is a fixed-size RelativeMove, so a dropped connection can't
leave the camera panning. Requests are serialized and rate-limited.
"""
import base64
import datetime
import hashlib
import html
import os
import re
import threading
import time
import urllib.error
import urllib.request

_WSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
_WSU = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
_PW_DIGEST = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest"
_B64 = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary"
_PTZ_NS = "http://www.onvif.org/ver20/ptz/wsdl"
_TT_NS = "http://www.onvif.org/ver10/schema"
_SERVICE = "/onvif/service"

PRESET_NAME = re.compile(r"^[A-Za-z0-9 _-]{1,32}$")
TOKEN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class PTZError(Exception):
    pass


class PTZInputError(PTZError):
    """The request itself was invalid (bad step, preset name or token); nothing was sent."""


class OnvifPTZ:
    def __init__(self, host, user, password, port=2020, timeout=8.0, min_interval=0.3):
        self._base = f"http://{host}:{port}"
        self._user = user
        self._password = password
        self._timeout = timeout
        self._min_interval = min_interval
        self._lock = threading.Lock()
        self._last = 0.0
        self._profile = None

    # ---- SOAP plumbing ----
    def _envelope(self, body):
        nonce = os.urandom(16)
        now = datetime.datetime.now(datetime.timezone.utc)  # noqa: UP017 - datetime.UTC needs Python 3.11
        created = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        # WS-Security UsernameToken digest is defined by the spec as SHA-1; it isn't our choice.
        raw = nonce + created.encode() + self._password.encode()
        digest = base64.b64encode(hashlib.sha1(raw).digest()).decode()  # nosec B324
        return (
            '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Header>'
            f'<Security xmlns="{_WSSE}"><UsernameToken>'
            f"<Username>{html.escape(self._user)}</Username>"
            f'<Password Type="{_PW_DIGEST}">{digest}</Password>'
            f'<Nonce EncodingType="{_B64}">{base64.b64encode(nonce).decode()}</Nonce>'
            f'<Created xmlns="{_WSU}">{created}</Created>'
            f"</UsernameToken></Security></s:Header><s:Body>{body}</s:Body></s:Envelope>"
        ).encode()

    def _call(self, body):
        req = urllib.request.Request(self._base + _SERVICE, data=self._envelope(body),
                                     headers={"Content-Type": "application/soap+xml; charset=utf-8"})
        try:
            # Fixed http:// base built from the configured camera host.
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # nosec B310
                return resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            reason = re.findall(r"<[^>]*:Text[^>]*>([^<]*)<", e.read().decode("utf-8", "replace"))
            raise PTZError(reason[0] if reason else f"camera returned HTTP {e.code}") from None
        except OSError as e:
            raise PTZError(f"camera unreachable: {getattr(e, 'reason', e)}") from None

    def _profile_token(self):
        if self._profile is None:
            xml = self._call('<GetProfiles xmlns="http://www.onvif.org/ver10/media/wsdl"/>')
            profiles = re.findall(r'<[^>]*:Profiles[^>]*token="([^"]+)"[^>]*>(.*?)</[^>]*:Profiles>', xml, re.S)
            for token, block in profiles:
                if "PTZConfiguration" in block:
                    self._profile = token
                    break
            if self._profile is None:
                raise PTZError("camera has no PTZ profile")
        return self._profile

    def _ptz(self, op, inner=""):
        return self._call(f'<{op} xmlns="{_PTZ_NS}"><ProfileToken>{self._profile_token()}</ProfileToken>{inner}</{op}>')

    def _throttle(self):
        wait = self._min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    # ---- operations ----
    def status(self):
        with self._lock:
            xml = self._ptz("GetStatus")
        pos = re.search(r'PanTilt[^>]*x="([-\d.eE]+)"[^>]*y="([-\d.eE]+)"', xml)
        moving = re.search(r"<[^>]*:PanTilt>(\w+)</[^>]*:PanTilt>", xml)
        return {
            "pan": float(pos.group(1)) if pos else None,
            "tilt": float(pos.group(2)) if pos else None,
            "moving": bool(moving and moving.group(1).upper() == "MOVING"),
        }

    def presets(self):
        with self._lock:
            xml = self._ptz("GetPresets")
        out = []
        for token, block in re.findall(r'<[^>]*:Preset[^>]*token="([^"]+)"[^>]*>(.*?)</[^>]*:Preset>', xml, re.S):
            name = re.search(r"<[^>]*:Name>([^<]*)<", block)
            out.append({"token": token, "name": html.unescape(name.group(1)) if name else token})
        return out

    def nudge(self, dx, dy):
        """Relative move in ONVIF's generic space (-1..1 covers the full range)."""
        if not (-1 <= dx <= 1 and -1 <= dy <= 1):
            raise PTZInputError("step out of range")
        with self._lock:
            self._throttle()
            move = f'<PanTilt xmlns="{_TT_NS}" x="{dx:.4f}" y="{dy:.4f}"/>'
            self._ptz("RelativeMove", f"<Translation>{move}</Translation>")

    def absolute(self, pan, tilt):
        if not (-1 <= pan <= 1 and -1 <= tilt <= 1):
            raise PTZInputError("position out of range")
        with self._lock:
            self._throttle()
            self._ptz("AbsoluteMove", f'<Position><PanTilt xmlns="{_TT_NS}" x="{pan:.6f}" y="{tilt:.6f}"/></Position>')

    def goto_preset(self, token):
        if not TOKEN.match(token or ""):
            raise PTZInputError("bad preset")
        with self._lock:
            self._throttle()
            self._ptz("GotoPreset", f"<PresetToken>{token}</PresetToken>")

    def save_preset(self, name):
        if not PRESET_NAME.match(name or ""):
            raise PTZInputError("preset names are 1-32 letters, numbers, spaces, - or _")
        with self._lock:
            xml = self._ptz("SetPreset", f"<PresetName>{html.escape(name)}</PresetName>")
        token = re.search(r"<[^>]*:PresetToken>([^<]+)<", xml)
        return token.group(1) if token else None
