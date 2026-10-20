"""Collect results/<method>/<split>.json into results/summary.md, one table per split.

Usage: python -m src.summarize
"""
import json
from pathlib import Path

from src.data import SPLITS
from src.evaluate import METRICS

ORDER = ["drain", "base_zeroshot", "base_fewshot"]  # baselines first, then fine-tuned runs alphabetically


def summary(root=Path("results")):
    methods = sorted((d.name for d in root.iterdir() if d.is_dir()),
                     key=lambda m: (ORDER.index(m) if m in ORDER else len(ORDER), m))
    out = ["# Results (macro-average over systems)", ""]
    for split in SPLITS:
        out += [f"## {split}", "", "| method | " + " | ".join(METRICS) + " |", "|---|" + "---|" * len(METRICS)]
        for m in methods:
            f = root / m / f"{split}.json"
            if f.exists():
                avg = json.loads(f.read_text())["average"]
                out.append(f"| {m} | " + " | ".join(f"{avg[k]:.3f}" for k in METRICS) + " |")
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    Path("results/summary.md").write_text(summary())
    print(summary())
