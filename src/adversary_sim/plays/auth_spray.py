
import os
import time
from typing import Any, Dict, List

from ..core import Context, Play


class AuthSpraySynthetic(Play):
    id = "auth_spray_lab"
    def __init__(self, spec=None):
        super().__init__(spec)
        self.log_path = spec.get("log_path", "lab_logs/auth.log")
        self.attempts = int(spec.get("attempts", 10))
        self.usernames: List[str] = spec.get("usernames", ["labuser","dev"])
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def preflight(self, ctx: Context):
        pass

    def run(self, ctx: Context) -> Dict[str, Any]:
        t0 = time.time()
        with open(self.log_path, "a", encoding="utf-8") as f:
            for i in range(self.attempts):
                user = self.usernames[i % len(self.usernames)]
                line = f"FAKE-SSH-FAIL user={user} ip=127.0.0.1 ts={time.time()}\n"
                f.write(line)
                time.sleep(0.1)
        return {"log_path": self.log_path, "attempts": self.attempts, "duration_s": round(time.time()-t0,2)}

    def expected_signals(self):
        return ["SIEM: spike in failed auth events", "Alert: password spraying (lab)"]

def create(spec):
    return AuthSpraySynthetic(spec)
