import pandas as pd
import pytest

from src.prepare_data import build_splits, check_no_leak, write_jsonl

CFG = {"seed": 42, "heldout_systems": ["H"], "per_template_cap": 3,
       "template_disjoint_train_frac": 0.7, "max_tokens": 400, "val_lines": 50}


def fake_df():
    rows = [(s, f"{s} msg {t} id {i}", f"{s} msg {t} id <*>")
            for s in "ABCH" for t in range(30) for i in range(6)]
    return pd.DataFrame(rows, columns=["system", "content", "template"])


def test_same_seed_gives_identical_files(tmp_path):
    for run in ("a", "b"):
        splits, _ = build_splits(fake_df(), CFG)
        (tmp_path / run).mkdir()
        for name, part in splits.items():
            write_jsonl(part, tmp_path / run / f"{name}.jsonl")
    for name in ("train", "val", "test_heldout", "test_template_disjoint"):
        assert (tmp_path / "a" / f"{name}.jsonl").read_bytes() == (tmp_path / "b" / f"{name}.jsonl").read_bytes()


def test_leak_assert_triggers_on_leaky_split():
    train = fake_df().query("system == 'A'")
    leaky_test = train.head(5)
    with pytest.raises(AssertionError, match="also in train"):
        check_no_leak(train, {"test": leaky_test})


def test_heldout_system_absent_from_train_and_val():
    splits, _ = build_splits(fake_df(), CFG)
    assert splits["test_heldout"].system.unique().tolist() == ["H"]
    for name in ("train", "val", "test_template_disjoint"):
        assert "H" not in set(splits[name].system)
    assert not set(splits["train"].template) & set(splits["val"].template)
