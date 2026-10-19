"""Build train/val/test JSONL from the Loghub-2k labelled CSVs.

Usage: python -m src.prepare_data --config configs/split.yaml
"""
import argparse
import json
import random
import sys
from pathlib import Path

import pandas as pd
import yaml

from src.prompt import to_example

RAW = Path("data/raw/2k_dataset")
OUT = Path("data/processed")
REPORT = Path("reports/data_card.md")
VAL_TEMPLATE_FRAC = 0.1  # share of train-candidate templates carved out for validation

try:
    from third_party.loghub2_eval.post_process import post_process
except ImportError:
    # shortcut: identity until the evaluator is vendored (Step 1.2); rerun once it is, or targets drift from the evaluator's style
    print("WARNING: post_process not vendored, templates are NOT normalised", file=sys.stderr)

    def post_process(t):
        return t


def load_system(name):
    df = pd.read_csv(RAW / name / f"{name}_2k.log_structured_corrected.csv",
                     usecols=["Content", "EventTemplate"], dtype=str, keep_default_na=False)
    return pd.DataFrame({"system": name, "content": df.Content, "template": df.EventTemplate})


def normalize(template):
    return post_process(template)


def dedupe(df):
    return df.drop_duplicates(["system", "content"]).reset_index(drop=True)


def n_tokens(text):
    # shortcut: whitespace tokens, not the model tokenizer; swap for the real one once chosen
    return len(text.split())


def split_templates(templates, frac, rng):
    """Template-disjoint split of one system's unique templates."""
    ts = sorted(set(templates))
    rng.shuffle(ts)
    k = round(len(ts) * frac)
    return set(ts[:k]), set(ts[k:])


def check_no_leak(train, tests):
    """Assert no template of any test split appears in train. `train` is a DataFrame; `tests` maps name -> DataFrame."""
    train_templates = set(train.template)
    for name, split in tests.items():
        leaked = set(split.template) & train_templates
        assert not leaked, f"{name}: {len(leaked)} templates also in train, e.g. {list(leaked)[:3]}"


def build_splits(df, cfg):
    rng = random.Random(cfg["seed"])
    held = set(cfg["heldout_systems"])
    test_heldout = df[df.system.isin(held)]
    train_parts, val_parts, test_td_parts = [], [], []
    for system in sorted(set(df.system) - held):
        sdf = df[df.system == system]
        train_c, td = split_templates(sdf.template, cfg["template_disjoint_train_frac"], rng)
        val_t, train_t = split_templates(train_c, VAL_TEMPLATE_FRAC, rng)
        train_parts.append(sdf[sdf.template.isin(train_t)])
        val_parts.append(sdf[sdf.template.isin(val_t)])
        test_td_parts.append(sdf[sdf.template.isin(td)])
    train, val, test_td = (pd.concat(p) for p in (train_parts, val_parts, test_td_parts))

    # cross-system leakage decision: a template string shared with any test/val split is dropped from train
    forbidden = set(test_heldout.template) | set(test_td.template) | set(val.template)
    dropped_shared = int(train.template.isin(forbidden).sum())
    train = train[~train.template.isin(forbidden)]

    train = train.sample(frac=1, random_state=cfg["seed"]).groupby(["system", "template"]).head(cfg["per_template_cap"])
    mt = cfg["max_tokens"]
    train = train[train.content.map(n_tokens) <= mt]
    val = val[val.content.map(n_tokens) <= mt]
    val = val.sample(min(len(val), cfg["val_lines"]), random_state=cfg["seed"])

    tests = {"test_heldout": test_heldout, "test_template_disjoint": test_td}
    check_no_leak(train, {**tests, "val": val})
    return {"train": train, "val": val, **tests}, dropped_shared


def write_jsonl(df, path):
    df = df.sort_values(["system", "content"])
    with open(path, "w") as f:
        for r in df.itertuples():
            f.write(json.dumps(to_example(r.system, r.content, r.template), ensure_ascii=False) + "\n")


def data_card(splits, dropped_shared):
    lines = ["# Data card", "",
             f"Train lines dropped because their template also occurs in val/test: {dropped_shared}", ""]
    for name, df in splits.items():
        lens = df.content.map(n_tokens)
        lines += [f"## {name}", f"{len(df)} lines, {df.template.nunique()} templates, "
                  f"tokens p50/p95/max: {lens.quantile(.5):.0f}/{lens.quantile(.95):.0f}/{lens.max()}", "",
                  "| system | lines | templates |", "|---|---|---|"]
        g = df.groupby("system").template.agg(["size", "nunique"])
        lines += [f"| {s} | {r['size']} | {r['nunique']} |" for s, r in g.iterrows()]
        lines += ["", "Top-10 templates:", ""]
        lines += [f"- {c} × `{t}`" for t, c in df.template.value_counts().head(10).items()] + [""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/split.yaml")
    cfg = yaml.safe_load(open(ap.parse_args().config))
    systems = sorted(p.name for p in RAW.iterdir() if p.is_dir())
    df = pd.concat([load_system(s) for s in systems])
    df["template"] = df.template.map(normalize)
    splits, dropped_shared = build_splits(dedupe(df), cfg)
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    for name, part in splits.items():
        write_jsonl(part, OUT / f"{name}.jsonl")
    REPORT.write_text(data_card(splits, dropped_shared))
    print({k: len(v) for k, v in splits.items()}, "dropped_shared:", dropped_shared)


if __name__ == "__main__":
    main()