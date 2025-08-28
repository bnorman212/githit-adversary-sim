
import importlib
import ipaddress
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

RFC1918 = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
]

def _is_private_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return any(ip in net for net in RFC1918)
    except ValueError:
        return host in ("localhost",)

def _url_is_private(url: str) -> bool:
    p = urlparse(url)
    host = p.hostname or ""
    if host in ("localhost",):
        return True
    try:
        ipaddress.ip_address(host)
        return any(ip in net for net in RFC1918)
    except Exception:
        return False

@dataclass
class Context:
    run_id: str
    labels: Dict[str, Any]
    pacing: Dict[str, Any]
    scope_allowlist: List[str]
    out_dir: str = "runs"

    def in_scope(self, host: str) -> bool:
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return host in ("localhost",)
        nets = [ipaddress.ip_network(c) for c in self.scope_allowlist]
        return any(ip in n for n in nets)

class Play:
    id = "base"
    def __init__(self, spec: Dict[str, Any] | None = None):
        self.spec = spec or {}
    def preflight(self, ctx: Context): ...
    def run(self, ctx: Context) -> Dict[str, Any]: ...
    def cleanup(self, ctx: Context): ...
    def expected_signals(self) -> List[str]: return []

def require_consent():
    if os.getenv("I_UNDERSTAND_AND_HAVE_PERMISSION") != "YES":
        print("[ABORT] Consent not provided. Set I_UNDERSTAND_AND_HAVE_PERMISSION=YES.", file=sys.stderr)
        sys.exit(2)

def load_config(path: str) -> Dict[str, Any]:
    if path.lower().endswith(".json"):
        return json.load(open(path, "r", encoding="utf-8"))
    try:
        import yaml
        return yaml.safe_load(open(path, "r", encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Failed to parse config {path}. For YAML, install pyyaml. ({e})", file=sys.stderr)
        sys.exit(2)

def load_play(module_path: str, spec: Dict[str, Any]) -> Play:
    mod = importlib.import_module(module_path)
    if hasattr(mod, "create"):
        return mod.create(spec)
    if hasattr(mod, "PLAY"):
        return getattr(mod, "PLAY")
    raise ValueError(f"Module {module_path} does not expose create() or PLAY")

def ensure_dir(p: str):
    Path(p).mkdir(parents=True, exist_ok=True)

def save_run(ctx: Context, summary: Dict[str, Any]):
    ensure_dir(ctx.out_dir)
    out_path = f"{ctx.out_dir}/{ctx.run_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return out_path

def guard_target_host(host: str, ctx: Context):
    if host in ("localhost",):
        return
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if host != "localhost":
            raise SystemExit(f"[DENY] Non-private hostname not allowed: {host}")
        return
    if not any(ip in net for net in RFC1918):
        raise SystemExit(f"[DENY] Target host must be RFC1918/localhost, got {host}")
    if not ctx.in_scope(host):
        raise SystemExit(f"[DENY] {host} not in scope_allowlist")

def guard_target_url(url: str, ctx: Context):
    if not _url_is_private(url):
        raise SystemExit(f"[DENY] URL host must be private/localhost for lab use: {url}")
    host = (urlparse(url).hostname or "")
    try:
        ipaddress.ip_address(host)  # validate IP (no need to assign)
        if not ctx.in_scope(host):
            raise SystemExit(f"[DENY] URL host {host} not in scope_allowlist")
    except ValueError:
        if host not in ("localhost",):
            raise SystemExit(f"[DENY] Non-private hostname not allowed: {host}")

    except ValueError:
        if host not in ("localhost",):
            raise SystemExit(f"[DENY] Non-private hostname not allowed: {host}")
