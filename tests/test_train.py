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
