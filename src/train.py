"""Fine-tune a LoRA adapter with Unsloth + TRL; loss is computed on the response only.

Usage: python -m src.train --config configs/qwen3_4b_r16.yaml
"""
import argparse
import json
import time
from pathlib import Path

import yaml

from src.data import load_split
from src.predict import _generate_hf, clean
from src.prompt import prompt_messages
from third_party.loghub2_eval.post_process import post_process

# Qwen chat-template turn markers; train_on_responses_only masks everything outside the assistant turn
INSTRUCTION_PART = "<|im_start|>user\n"
RESPONSE_PART = "<|im_start|>assistant\n"


def check_data_paths(cfg):
    """Training and tuning must never read a test split."""
    for key in ("train", "val"):
        name = Path(cfg["data"][key]).name
        assert "test" not in name, f"data.{key} must be a train/val file, got {name}"


def persistent_run_id(out, make_id):
    """W&B run id stored beside the checkpoints: a resumed run reuses it, a fresh output dir gets a new one.

    A fixed id (the run name) collides with any earlier run of the same name ("run ID ... is in use").
    """
    out.mkdir(parents=True, exist_ok=True)
    f = out / "wandb_id.txt"
    if not f.exists():
        f.write_text(make_id())
    return f.read_text().strip()


def render(tok, messages):
    """Training text = the inference prompt + the answer + EOS.

    The Qwen template renders a final assistant turn as "<think>\n\n</think>\n\n<answer>", but the generation prompt
    never supplies that block, so the model would learn to open with it and clean() would return "<think>".
    """
    *prompt, answer = messages
    return tok.apply_chat_template(prompt, tokenize=False, add_generation_prompt=True) + answer["content"] + tok.eos_token


def without_system_line(messages):
    """Training messages with the 'System: X' line dropped from the user turn (the system_line=False prompt)."""
    out = [dict(m) for m in messages]
    user = next(m for m in out if m["role"] == "user")
    user["content"] = user["content"].split("\n", 1)[1]
    return out


def fitting_rows(tok, rows, max_len, system_line=True):
    """Rows whose prompt + answer fit in max_len tokens, i.e. the ones the trainer keeps; one very long line
    padded into a generation batch otherwise runs the GPU out of memory."""
    fits = [len(tok(render(tok, [*prompt_messages(s, c, system_line=system_line),
                                 {"role": "assistant", "content": g}]))["input_ids"]) <= max_len
            for s, c, g in zip(rows.system, rows.content, rows.gold)]
    print(f"val_pa uses {sum(fits)} of {len(fits)} lines (the rest exceed max_seq_length)")
    return rows[fits]


def val_correct(gen, rows, system_line=True):
    """Per-line exact match after clean() and post_process. `gen(msgs) -> raw outputs`; rows has system, content, gold."""
    msgs = [prompt_messages(s, c, system_line=system_line) for s, c in zip(rows.system, rows.content)]
    raw = gen(msgs)
    assert len(raw) == len(rows)
    return [post_process(clean(r)) == post_process(g) for r, g in zip(raw, rows.gold)]


def val_pa(gen, rows, system_line=True):
    ok = val_correct(gen, rows, system_line)
    return sum(ok) / len(ok)


def val_pa_callback(rows, history_path, system_line=True):
    from transformers import TrainerCallback
    from unsloth import FastLanguageModel

    class ValPA(TrainerCallback):
        # step -> {"val_pa", "val_pa_macro", "by_system", "eval_loss"}; kept on disk so a resumed run does not lose earlier evals
        history = json.loads(history_path.read_text()) if history_path.exists() else {}

        def on_evaluate(self, args, state, control, model=None, metrics=None, **kw):
            tok = kw.get("processing_class") or kw.get("tokenizer")
            FastLanguageModel.for_inference(model)
            side, tok.padding_side = tok.padding_side, "left"
            raw = []

            def gen(msgs):
                raw.extend(_generate_hf(model, tok, msgs))
                return raw

            try:
                ok = val_correct(gen, rows, system_line)
            finally:
                tok.padding_side = side
                FastLanguageModel.for_training(model)
            by_system = rows.assign(ok=ok).groupby("system").ok.mean().to_dict()
            pa, macro = sum(ok) / len(ok), sum(by_system.values()) / len(by_system)
            # evaluate() returns this same dict, so the Trainer's best-model and early-stopping logic sees it
            metrics["eval_val_pa"], metrics["eval_val_pa_macro"] = pa, macro
            self.history[str(state.global_step)] = {"val_pa": pa, "val_pa_macro": macro, "by_system": by_system,
                                                    "eval_loss": metrics.get("eval_loss")}
            history_path.write_text(json.dumps(self.history, indent=2))
            print(f"step {state.global_step}: val_pa={pa:.3f} macro={macro:.3f} "
                  + " ".join(f"{k}={v:.2f}" for k, v in sorted(by_system.items())))
            for r, g in [(r, g) for r, g, o in zip(raw, rows.gold, ok) if not o][:3]:  # what the model gets wrong
                print(f"  wrong: raw={r!r} gold={g!r}")
            import wandb
            if wandb.run:  # the Trainer logged its eval metrics before this callback ran
                wandb.log({"eval/val_pa": pa, "eval/val_pa_macro": macro, "train/global_step": state.global_step,
                           **{f"eval/val_pa_sys/{k}": v for k, v in by_system.items()}})

    return ValPA()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = yaml.safe_load(Path(ap.parse_args().config).read_text())
    check_data_paths(cfg)
    t, lo = cfg["train"], cfg["lora"]

    from unsloth import FastLanguageModel  # must be imported before transformers/trl
    from unsloth.chat_templates import train_on_responses_only
    import torch
    import wandb
    from datasets import load_dataset
    from transformers import EarlyStoppingCallback
    from transformers.trainer_utils import get_last_checkpoint
    from trl import SFTConfig, SFTTrainer

    t0 = time.time()
    out = Path(cfg["output_dir"])
    wandb.init(project=cfg["wandb_project"], name=cfg["run_name"], config=cfg, resume="allow",
               id=persistent_run_id(out, wandb.util.generate_id))

    try:
        # Stage 1: load and wrap
        model, tok = FastLanguageModel.from_pretrained(
            cfg["model"], max_seq_length=cfg["max_seq_length"], load_in_4bit=cfg["load_in_4bit"])
        model = FastLanguageModel.get_peft_model(
            model, r=lo["r"], lora_alpha=lo["alpha"], lora_dropout=lo["dropout"], target_modules=lo["target_modules"],
            bias="none", use_gradient_checkpointing="unsloth", random_state=t["seed"])
        model.print_trainable_parameters()

        # Stage 2: data -> text. TRL treats a dataset with a "messages" column as conversational and would ignore
        # "text", so drop it. render() ends the text with EOS, so TRL does not append a second one.
        ds = load_dataset("json", data_files={"train": cfg["data"]["train"], "val": cfg["data"]["val"]})
        if cfg["data"].get("max_train_examples"):
            ds["train"] = ds["train"].select(range(cfg["data"]["max_train_examples"]))
        system_line = cfg.get("system_line", True)
        ds = ds.map(lambda ex: {"text": render(tok, ex["messages"] if system_line else without_system_line(ex["messages"]))},
                    remove_columns=["messages"])

        # Stage 3: trainer with response-only loss
        trainer = SFTTrainer(
            model=model, processing_class=tok, train_dataset=ds["train"], eval_dataset=ds["val"],
            # Stage 4: val_pa must run before EarlyStopping so the metric is in the dict it reads
            callbacks=[val_pa_callback(
                fitting_rows(tok, load_split(Path(cfg["data"]["val"])).head(cfg["val_pa_lines"]),
                             cfg["max_seq_length"], system_line),
                out / "val_history.json", system_line),
                       EarlyStoppingCallback(early_stopping_patience=t["early_stopping_patience"])],
            args=SFTConfig(
                output_dir=cfg["output_dir"], run_name=cfg["run_name"], report_to="wandb", seed=t["seed"],
                per_device_train_batch_size=t["per_device_batch_size"], per_device_eval_batch_size=t["per_device_batch_size"],
                gradient_accumulation_steps=t["grad_accum"], learning_rate=t["lr"], num_train_epochs=t["epochs"],
                max_steps=t.get("max_steps", -1), warmup_ratio=t["warmup_ratio"], lr_scheduler_type=t["scheduler"],
                optim=t["optim"], fp16=t["fp16"], bf16=t["bf16"], logging_steps=5,
                eval_strategy="steps", eval_steps=t["eval_steps"], save_strategy="steps", save_steps=t["save_steps"],
                save_total_limit=3, load_best_model_at_end=True, metric_for_best_model="val_pa", greater_is_better=True,
                dataset_text_field="text", max_length=cfg["max_seq_length"], packing=False))
        trainer = train_on_responses_only(trainer, instruction_part=INSTRUCTION_PART, response_part=RESPONSE_PART)

        labels = [x for x in trainer.train_dataset[0]["labels"] if x != -100]
        shown = tok.decode(labels)
        print("loss is computed on:", repr(shown))
        assert shown.strip() and "<|im_start|>" not in shown and "<think>" not in shown, \
            "loss mask is wrong: the prompt or a think block is in the labels"

        # Stage 5: resume if a checkpoint exists, then report
        trainer.train(resume_from_checkpoint=get_last_checkpoint(out))

        peak = torch.cuda.max_memory_allocated() / 2**30
        stats = {"peak_vram_gb": peak, "wall_time_min": (time.time() - t0) / 60,
                 "best_val_pa": trainer.state.best_metric, "best_checkpoint": trainer.state.best_model_checkpoint}
        wandb.summary.update(stats)
        print(stats)
        best = trainer.state.best_model_checkpoint
        (out / "result.json").write_text(json.dumps({
            "run_name": cfg["run_name"], "config": cfg, **stats,
            "best_step": int(best.rsplit("-", 1)[1]) if best else None,
            "history": json.loads((out / "val_history.json").read_text())}, indent=2))
        model.save_pretrained(out / "best")
        tok.save_pretrained(out / "best")
    finally:
        # a run left open keeps its id "in use" in Colab's shared wandb service, so a rerun or resume would fail
        wandb.finish()


if __name__ == "__main__":
    main()
