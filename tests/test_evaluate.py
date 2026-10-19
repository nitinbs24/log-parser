import pandas as pd

from src.evaluate import score

GOLD = pd.read_csv("data/handcrafted/benchmark.csv", dtype=str, keep_default_na=False)


def test_gold_scores_perfect():
    res = score(GOLD.assign(pred=GOLD.gold))
    assert all(res["average"][m] == 1.0 for m in ("GA", "FGA", "PA", "FTA"))


def test_all_wildcard_scores_low():
    res = score(GOLD.assign(pred="<*>"))["average"]
    assert res["PA"] < 0.05 and res["GA"] < 0.2 and res["FTA"] < 0.1
