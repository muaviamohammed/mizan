"""Attach your stapled MIZAN proof to every response, in one line. Buyers verify it locally: zero calls to MIZAN.

    from mizan.staple import MizanStaple
    app = MizanStaple(app, identity="0xYourPayoutWallet")    # any ASGI app: FastAPI, Starlette, …

Fetches a receipt bound to `identity` from MIZAN (only issued if that identity passes), caches it, refreshes it an
hour before it expires, and adds `X-Mizan-Receipt` to every HTTP response. If MIZAN is unreachable or the identity is
not proven, responses go out unchanged (it never blocks your service). Stdlib only.
"""
import json, threading, time, urllib.request

STUDIO = "https://studio.mizan.market"


class MizanStaple:
    def __init__(self, app, identity: str, refresh_margin: int = 3600):
        self.app, self.identity, self.margin = app, identity, refresh_margin
        self._tok, self._exp, self._next_try, self._lock = None, 0, 0, threading.Lock()

    def receipt(self):
        now = time.time()
        if self._tok and now < self._exp - self.margin:
            return self._tok
        if now < self._next_try:
            return self._tok if self._tok and now < self._exp else None
        with self._lock:
            try:
                req = urllib.request.Request(f"{STUDIO}/api/staple/{self.identity}", headers={"User-Agent": "mizan-staple/1"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    d = json.loads(r.read())
                if d.get("ok"):
                    self._tok, self._exp = d["receipt"], d["payload"]["exp"]
                self._next_try = now + 300
            except Exception:
                self._next_try = now + 300
        return self._tok if self._tok and now < self._exp else None

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        tok = self.receipt()

        async def send2(msg):
            if tok and msg.get("type") == "http.response.start":
                msg = dict(msg); msg["headers"] = list(msg.get("headers", [])) + [(b"x-mizan-receipt", tok.encode())]
            await send(msg)
        return await self.app(scope, receive, send2)
