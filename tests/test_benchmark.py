import csv
import re
from pathlib import Path

BENCH = Path(__file__).parent.parent / "data" / "handcrafted" / "benchmark.csv"


def _regex(gold):
    return re.compile("".join(".+?" if p == "<*>" else re.escape(p) for p in re.split(r"(<\*>)", gold)), re.S)


def test_benchmark_gold_matches_content():
    rows = list(csv.DictReader(open(BENCH, newline="")))
    assert len(rows) >= 30
    for r in rows:
        assert r["gold"].strip(), r
        assert _regex(r["gold"]).fullmatch(r["content"]), r
