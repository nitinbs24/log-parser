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


def test_val_lines_per_template_are_capped():
    splits, _ = build_splits(fake_df(), CFG)
    per_template = splits["val"].groupby(["system", "template"]).size()
    assert len(per_template) and per_template.max() <= CFG["per_template_cap"]


def test_train_cap_raises_train_only():
    small, _ = build_splits(fake_df(), CFG)
    big, _ = build_splits(fake_df(), {**CFG, "train_cap": 5})
    assert big["train"].groupby(["system", "template"]).size().max() == 5
    assert set(small["train"].content) < set(big["train"].content)  # cap-3 lines are a subset
    for name in ("val", "test_heldout", "test_template_disjoint"):
        assert big[name].equals(small[name])
