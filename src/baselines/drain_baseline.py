"""B0: run logparser3's Drain per system on each test split and score it with src.evaluate.

Usage: python -m src.baselines.drain_baseline
Writes results/drain/<split>.csv (system, content, gold, pred) and results/drain/<split>.json.
"""
import json
import tempfile
from pathlib import Path

import pandas as pd
from logparser.Drain import LogParser

from src.data import SPLITS, load_split
from src.evaluate import METRICS, score

OUT = Path("results/drain")
DEPTH, ST = 4, 0.5  # Drain defaults from the Loghub-2.0 benchmark


def drain_templates(contents):
    """One template per input line, in order. Drain is per-system, so call it with one system's lines."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "x.log").write_text("\n".join(contents) + "\n")
        LogParser(log_format="<Content>", indir=tmp, outdir=tmp, depth=DEPTH, st=ST, rex=[]).parse("x.log")
        out = pd.read_csv(Path(tmp) / "x.log_structured.csv", dtype=str, keep_default_na=False)
    assert len(out) == len(contents), f"Drain returned {len(out)} rows for {len(contents)} lines"
    return out["EventTemplate"].tolist()


def predict(df):
    pred = pd.Series("", index=df.index)
    for _, g in df.groupby("system"):
        pred[g.index] = drain_templates(g.content.tolist())
    return df.assign(pred=pred)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, path in SPLITS.items():
        df = predict(load_split(path))
        df.to_csv(OUT / f"{name}.csv", index=False)
        res = score(df)
        (OUT / f"{name}.json").write_text(json.dumps(res, indent=2))
        print(f"== {name}: " + " ".join(f"{m}={res['average'][m]:.3f}" for m in METRICS))


if __name__ == "__main__":
    main()
