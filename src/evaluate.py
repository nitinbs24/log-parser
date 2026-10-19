"""Score a predictions CSV with the Loghub-2.0 metrics (GA, FGA, PA, FTA), per system and macro-averaged.

Usage: python -m src.evaluate --pred predictions.csv --out results/<model>/<split>.json
Input columns: system, content, gold, pred.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from third_party.loghub2_eval.PA_calculator import calculate_parsing_accuracy
from third_party.loghub2_eval.evaluator import evaluate as grouping_scores
from third_party.loghub2_eval.post_process import post_process
from third_party.loghub2_eval.template_level_analysis import evaluate_template_level

METRICS = ["GA", "FGA", "PA", "FTA"]


def score_system(name, content, gold, pred):
    gt = pd.DataFrame({"Content": content, "EventTemplate": [post_process(g) for g in gold]})
    pr = pd.DataFrame({"Content": content, "EventTemplate": [post_process(str(p)) for p in pred]})
    ga, fga = grouping_scores(gt, pr)
    pa = calculate_parsing_accuracy(gt, pr)
    _, _, fta, _, _ = evaluate_template_level(name, gt, pr)
    return dict(zip(METRICS, (ga, fga, pa, fta)), lines=len(gt))


def score(df):
    """df has system, content, gold, pred. Returns {"per_system": {...}, "average": {...}}."""
    per = {s: score_system(s, g.content.tolist(), g.gold.tolist(), g.pred.tolist())
           for s, g in df.groupby("system", sort=True)}
    avg = {m: sum(v[m] for v in per.values()) / len(per) for m in METRICS}
    return {"per_system": per, "average": avg}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    df = pd.read_csv(args.pred, dtype=str, keep_default_na=False)
    missing = {"system", "content", "gold", "pred"} - set(df.columns)
    assert not missing, f"{args.pred} is missing columns {sorted(missing)}"
    res = score(df)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2))
    for s, v in res["per_system"].items():
        print(f"{s:12s} " + " ".join(f"{m}={v[m]:.3f}" for m in METRICS))
    print(f"{'Average':12s} " + " ".join(f"{m}={res['average'][m]:.3f}" for m in METRICS))


if __name__ == "__main__":
    main()
