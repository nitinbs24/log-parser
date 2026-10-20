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


def test_render_is_the_inference_prompt_plus_answer_and_eos():
    from src.train import render

    class Tok:
        eos_token = "<|im_end|>"

        def apply_chat_template(self, msgs, tokenize, add_generation_prompt=False):
            out = "".join(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in msgs)
            if add_generation_prompt:
                out += "<|im_start|>assistant\n"
            return out

    msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}, {"role": "assistant", "content": "a <*>"}]
    text = render(Tok(), msgs)
    assert text == Tok().apply_chat_template(msgs[:-1], tokenize=False, add_generation_prompt=True) + "a <*><|im_end|>"
    assert "<think>" not in text


def test_wandb_id_is_new_per_fresh_dir_and_reused_on_resume(tmp_path):
    from src.train import persistent_run_id
    ids = iter(["aaa", "bbb"])
    d = tmp_path / "run"
    assert persistent_run_id(d, lambda: next(ids)) == "aaa"
    assert persistent_run_id(d, lambda: next(ids)) == "aaa"  # resume keeps the id
    assert persistent_run_id(tmp_path / "other", lambda: next(ids)) == "bbb"


def test_fitting_rows_drops_lines_longer_than_the_limit():
    from src.train import fitting_rows

    class Tok:  # one "token" per character
        eos_token = "|"

        def apply_chat_template(self, msgs, tokenize, add_generation_prompt=False):
            return "".join(m["content"] for m in msgs) + ("A" if add_generation_prompt else "")

        def __call__(self, text):
            return {"input_ids": list(text)}

    rows = pd.DataFrame({"system": ["A", "B"], "content": ["short", "x" * 500], "gold": ["t", "t"]})
    kept = fitting_rows(Tok(), rows, max_len=300)
    assert list(kept.system) == ["A"]


def test_without_system_line_matches_the_prompt_builder():
    from src.prompt import prompt_messages, to_example
    from src.train import without_system_line
    full = to_example("Redis", "ready", "ready")["messages"]
    want = prompt_messages("Redis", "ready", system_line=False) + [{"role": "assistant", "content": "ready"}]
    assert without_system_line(full) == want
    assert full[1]["content"].startswith("System: Redis")  # the input is not modified


def test_val_correct_reports_each_line_and_respects_system_line():
    from src.train import val_correct
    seen = []
    ok = val_correct(lambda msgs: seen.extend(msgs) or ["a <*>", "wrong", "c <*>"], ROWS, system_line=False)
    assert ok == [True, False, True]
    assert seen[0][-1]["content"] == "Log: a 1"
