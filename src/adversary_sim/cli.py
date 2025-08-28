
import argparse
import time

from .core import Context, load_config, load_play, require_consent, save_run


def main():
    ap = argparse.ArgumentParser(description="GitHit! — Blue-team safe adversary simulator (lab only).")
    ap.add_argument("--config", required=True, help="Path to JSON/YAML config")
    args = ap.parse_args()

    require_consent()
    cfg = load_config(args.config)
    ctx = Context(
        run_id=cfg.get("run_id", f"sim-{int(time.time())}"),
        labels=cfg.get("labels", {}),
        pacing=cfg.get("pacing", {}),
        scope_allowlist=cfg.get("scope_allowlist", ["127.0.0.1/32"]),
        out_dir=cfg.get("out_dir", "runs"),
    )

    plays = cfg.get("plays", [])
    results = {"run_id": ctx.run_id, "labels": ctx.labels, "plays": []}
    for spec in plays:
        module = spec.get("module")
        pid = spec.get("id", module)
        print(f"[PLAY] {pid} -> {module}")
        play = load_play(module, spec)
        play.preflight(ctx)
        start = time.time()
        try:
            data = play.run(ctx) or {}
        finally:
            play.cleanup(ctx)
        dur = time.time() - start
        print(f"[OK] {pid} complete in {dur:.2f}s | expect: {play.expected_signals()}")
        results["plays"].append({
            "id": pid, "module": module, "duration_s": round(dur,2),
            "expected_signals": play.expected_signals(), "data": data
        })

    out_path = save_run(ctx, results)
    print(f"[SUMMARY] wrote {out_path}")
