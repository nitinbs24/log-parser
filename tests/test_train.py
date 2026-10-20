import pandas as pd
import pytest

from src.train import check_data_paths, val_pa

ROWS = pd.DataFrame({"system": ["A", "B", "C"], "content": ["a 1", "b 2", "c 3"],
                     "gold": ["a <*>", "b <*>", "c <*>"]})


def test_val_pa_counts_exact_matches_after_clean():
    raw = ["a <*>", "`b <*>`", "c <*> extra"]  # right, right after clean(), wrong
    assert val_pa(lambda msgs: raw, ROWS) == pytest.approx(2 / 3)


def test_val_pa_prompts_use_the_shared_prompt():
    seen = []
    val_pa(lambda msgs: seen.extend(msgs) or ["x"] * len(msgs), ROWS)
    assert seen[0][-1]["content"] == "System: A\nLog: a 1" and seen[0][0]["role"] == "system"


def test_training_cannot_read_a_test_split():
    ok = {"data": {"train": "data/processed/train.jsonl", "val": "data/processed/val.jsonl"}}
    check_data_paths(ok)
    with pytest.raises(AssertionError):
        check_data_paths({"data": {"train": "data/processed/train.jsonl", "val": "data/processed/test_heldout.jsonl"}})
