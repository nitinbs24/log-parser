"""One-axis-at-a-time hyperparameter sweep (walkthrough Step 4.4); tuned on validation only, never the held-out systems.

python -m src.sweep write             # generate configs/sweep/<run>.yaml from configs/sweep.yaml
python -m src.sweep run [name ...]    # train each run that has no result.json yet, one process per run
python -m src.sweep summary           # write reports/sweep.md from outputs/runs/sweep_*/result.json
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

import yaml

SPEC = Path("configs/sweep.yaml")
CONFIG_DIR = Path("configs/sweep")
RUNS = Path("outputs/runs")
NOISE = 2 / 58  # one validation line is worth 1/58; a gap under two lines is not a difference


def set_path(cfg, dotted, value):
    *parents, leaf = dotted.split(".")
    node = cfg
    for k in parents:
        node = node[k]
    node[leaf] = value


def make_configs(spec):
    base = yaml.safe_load(Path(spec["base"]).read_text())
    out = {}
    for name, overrides in spec["runs"].items():
        cfg = copy.deepcopy(base)
        for k, v in {**spec.get("common", {}), **overrides}.items():
            set_path(cfg, k, v)
        cfg["run_name"] = f"sweep_{name}"
        cfg["output_dir"] = f"outputs/runs/sweep_{name}"
        out[name] = cfg
    return out


def summary(runs_dir, order):
    rows = {}
    for name in order:
        f = runs_dir / f"sweep_{name}" / "result.json"
        if f.exists():
            r = json.loads(f.read_text())
            hist = r["history"]
            best = hist.get(str(r["best_step"]), {})
            rows[name] = {"best": r["best_val_pa"], "step": r["best_step"], "macro": best.get("val_pa_macro"),
                          "last": hist[str(max(map(int, hist)))]["val_pa"], "loss": min(h["eval_loss"] for h in hist.values()),
                          "min": r["wall_time_min"],
                          "vram": r["peak_vram_gb"], "by_system": best.get("by_system", {})}
    base = rows.get("default", {}).get("best")
    out = ["# Sweep (validation only; held-out systems untouched)", "",
           f"A validation line is worth about 1.7 points, so a gap under {NOISE:.3f} (two lines) is noise.", "",
           "val_pa tops out near 0.93 here (the last wrong lines are label conventions), so runs that tie on val_pa are ranked by"
           " the lower validation loss.", "",
           "| run | best val_pa | vs default | best step | macro at best | last val_pa | min eval_loss | min | peak GB |",
           "|---|---|---|---|---|---|---|---|---|"]
    for n, r in rows.items():
        d = "" if base is None or n == "default" else f"{r['best'] - base:+.3f}" + ("" if abs(r["best"] - base) >= NOISE else " (noise)")
        out.append(f"| {n} | {r['best']:.3f} | {d} | {r['step']} | {r['macro']:.3f} | {r['last']:.3f} | {r['loss']:.4f} | {r['min']:.1f} | {r['vram']:.1f} |")
    systems = sorted({s for r in rows.values() for s in r["by_system"]})
    out += ["", "## val_pa per system at the best step", "", "| run | " + " | ".join(systems) + " |", "|---|" + "---|" * len(systems)]
    for n, r in rows.items():
        out.append(f"| {n} | " + " | ".join(f"{r['by_system'][s]:.2f}" if s in r["by_system"] else "" for s in systems) + " |")
    return "\n".join(out) + "\n"


def main():
    cmd, names = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    spec = yaml.safe_load(SPEC.read_text())
    if cmd == "write":
        CONFIG_DIR.mkdir(exist_ok=True)
        for name, cfg in make_configs(spec).items():
            (CONFIG_DIR / f"{name}.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    elif cmd == "run":
        for name in names or spec["runs"]:
            if (RUNS / f"sweep_{name}" / "result.json").exists():
                print(f"skip {name}: already has a result")
                continue
            subprocess.run([sys.executable, "-m", "src.train", "--config", str(CONFIG_DIR / f"{name}.yaml")], check=True)
    elif cmd == "summary":
        Path("reports/sweep.md").write_text(summary(RUNS, list(spec["runs"])))
        print(Path("reports/sweep.md").read_text())
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
