
import os
import time
import urllib.request
from typing import Any, Dict

from ..core import Context, Play, guard_target_url


class ExfilLocalSink(Play):
    id = "exfil_local_sink"
    def __init__(self, spec=None):
        super().__init__(spec)
        self.target_url = spec.get("target_url", "http://127.0.0.1:8080/upload")
        self.bytes = int(spec.get("bytes", 256*1024))

    def preflight(self, ctx: Context):
        guard_target_url(self.target_url, ctx)

    def run(self, ctx: Context) -> Dict[str, Any]:
        data = os.urandom(self.bytes)
        start = time.time()
        req = urllib.request.Request(self.target_url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.status
            body = resp.read(128).decode("utf-8", errors="ignore")
        dur = time.time() - start
        return {
            "url": self.target_url,
            "bytes": self.bytes,
            "status": status,
            "duration_s": round(dur, 2),
            "preview": body,
        }


    def expected_signals(self):
        return ["Proxy/Firewall egress log", "DLP: outbound data event", "Sink HTTP access log"]

def create(spec):
    return ExfilLocalSink(spec)
