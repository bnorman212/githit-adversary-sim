
import socket
import time
from typing import Any, Dict, List

from ..core import Context, Play, guard_target_host


class ReconPlay(Play):
    id = "recon_local"
    def __init__(self, spec=None):
        super().__init__(spec)
        self.host = spec.get("target_host", "127.0.0.1")
        self.ports: List[int] = spec.get("ports", [22,80,443])
        self.timeout = float(spec.get("timeout", 0.5))
        self.delay = float(spec.get("delay", 0.05))

    def preflight(self, ctx: Context):
        guard_target_host(self.host, ctx)

    def run(self, ctx: Context) -> Dict[str, Any]:
        open_ports = []
        for p in self.ports:
            try:
                with socket.create_connection((self.host, p), timeout=self.timeout):
                    open_ports.append(p)
            except Exception:
                pass
            time.sleep(self.delay)
        return {"host": self.host, "scanned": self.ports, "open_ports": open_ports}

    def expected_signals(self):
        return ["IDS/Firewall: multiple TCP connections", "Service logs: potential banner/access"]

def create(spec):
    return ReconPlay(spec)
