"""Shared loaders for the evaluation splits."""
import json
import random
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


def few_shot_examples(k=5, seed=42, train_path=Path("data/processed/train.jsonl")):
    """k fixed (system, content, template) triples from k different training systems, each with a variable."""
    train = load_split(train_path)
    rng = random.Random(seed)
    systems = sorted(train.system.unique())
    rng.shuffle(systems)
    out = []
    for s in systems[:k]:
        g = train[(train.system == s) & train.gold.str.contains("<*>", regex=False)]
        r = g.iloc[rng.randrange(len(g))]
        out.append((s, r.content, r.gold))
    return out
