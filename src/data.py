"""Shared loaders for the evaluation splits."""
import json
from pathlib import Path

import pandas as pd

SPLITS = {
    "test_heldout": Path("data/processed/test_heldout.jsonl"),
    "test_template_disjoint": Path("data/processed/test_template_disjoint.jsonl"),
    "handcrafted": Path("data/handcrafted/benchmark.csv"),
}


def load_split(path):
    """Return a DataFrame with columns system, content, gold."""
    if path.suffix == ".csv":
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    rows = []
    for line in path.read_text().splitlines():
        _, user, assistant = json.loads(line)["messages"]
        head, content = user["content"].split("\nLog: ", 1)
        rows.append((head.removeprefix("System: "), content, assistant["content"]))
    return pd.DataFrame(rows, columns=["system", "content", "gold"])
