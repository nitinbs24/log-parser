# Implementation Plan: LoRA Log Parser

Source: [log-parsing-finetune-guide.md](log-parsing-finetune-guide.md) (goal, datasets, metrics, stack, repo layout). This plan orders the work; it does not repeat the guide's reasoning.

## Confirmed intent

- **Phase A (build first):** LoRA-fine-tune Qwen3-4B-Instruct-2507 to turn one log line into a template. Evaluate **model-only, per line** on Loghub-2k (cross-system held-out + template-disjoint) against Drain (B0), base zero-shot (B1), base few-shot (B2). No hybrid logic in Phase A.
- **Phase B (second):** Separate hybrid parser in `src/pipeline/` for real logs: pre-parse → Drain grouping → LLM on 2–3 sample lines per group → regex-validate each template against the whole group (re-parse misses individually) → template cache. Own system-level eval.
- **Phase C (later, placeholder only):** Kafka workers + Redis template store.
- **User:** learning first, but usable on own Kafka / Kubernetes / Nginx / PostgreSQL / Redis / OpenSearch logs, offline batches of thousands to a few million lines.
- **Out of scope:** streaming (Phase C), TPU, 8B sweeps, full Loghub-2.0 run, variable-extraction JSON, anomaly-detection payoff, second adapter.

## Constraints that shape every task

- All logic in `.py` files. Colab uses a thin launcher notebook (`git clone`, `!python …`, outputs symlinked to Drive). The same code runs unchanged on the college server (2×T4, vLLM).
- T4: `fp16=True`, `bf16=False`, no FlashAttention 2. Checkpoints to Drive, `save_steps` ~50, resume enabled, each run under ~1 h.
- `src/predict.py` exposes `parse_lines(lines: list[str]) -> list[str]` and a `--backend vllm|ollama` flag. Phase B imports it as-is.
- Same prompt for every model. Greedy decoding (`temperature=0`, `max_tokens=128`).
- Reuse the `logpai/loghub-2.0` evaluator and `post_process`. Do not reimplement the metrics.
- Pin versions in `requirements.txt` the day the stack first works.

## Dependency graph

```
T0 Setup/bootstrap
 └─ T1 Data prep + split + leakage assert ──────────────┐
     ├─ T2 Eval harness + Drain baseline (B0)           │
     │    └─ T3 predict.py (parse_lines, vllm) ─ T4 Base zero/few-shot (B1,B2)
     │                                            │
     ├─ T1b Handcrafted benchmark (parallel)      │
     └─ T5 train.py + 1 smoke run ── T6 Full run + eval vs B0–B2 ── T7 Sweep ── T8 Final eval suite
                                                                               ├─ T9 Forgetting check
                                                                               ├─ T10 Model-size table
                                                                               └─ T11 Export (adapter, GGUF) ── T12 Report
        ═══════════ Checkpoint A: Phase A complete ═══════════
T11 + T3 ─ B1 Pre-parser ─ B2 Group + LLM sample ─ B3 Regex validate + fallback ─ B4 Cache ─ B5 Batch CLI ─ B6 System eval ─ B7 Docs/compose
        ═══════════ Checkpoint B: Phase B complete ═══════════
Phase C placeholder
```

The order is a walking skeleton first: T1 → T2 → T3 → T5 gives one thin end-to-end path (data → train → predict → score) before any tuning.

---

## Phase 0: Setup

### T0. Repo skeleton and Colab bootstrap
**Do:** Create the layout from guide §9 (`configs/ src/ notebooks/ third_party/ results/ reports/ data/`), `.gitignore` (data/raw, outputs), `Makefile` stubs, and `notebooks/00_colab_bootstrap.ipynb` (mount Drive, clone, install pinned deps, W&B + HF login). Vendor `loghub-2.0` evaluator + `2k_dataset/` into `third_party/` with license and citation. Write `requirements.txt`.
**Accept:**
- [ ] Bootstrap notebook runs top to bottom on a fresh Colab T4 session without edits.
- [ ] Qwen3-4B loads in 4-bit and generates one reply on the T4.
- [ ] Output dir is a symlink into Drive; a file written there survives a runtime restart.
**Verify:** run the notebook on Colab; `nvidia-smi` shows <7 GB used after load.
**Size:** M

---

## Phase A: Fine-tune and evaluate (model-only)

### T1. Data prep, splits, leakage guard
**Do:** `src/prepare_data.py` reads the Loghub-2k structured CSVs (`Content` → `EventTemplate`), applies `post_process` to targets, dedupes on `(system, Content)`, caps ≤3 examples per template, drops lines over ~400 tokens, and writes `data/processed/{train,val,test_*}.jsonl` in the chat format from guide §8. `configs/split.yaml` holds held-out systems (OpenStack, Thunderbird, Mac, Proxifier), seed and cap. Add `reports/data_card.md` generation.
**Accept:**
- [ ] Train has ~1–2k examples from 12 systems; the 4 held-out systems never appear in train or val.
- [ ] Template-disjoint split exists (~70/30 of templates per training system).
- [ ] Assertion in code: no test template string occurs in any training target; the script fails loudly if it does.
- [ ] Data card lists lines and templates per system, per split, length distribution, template skew.
- [ ] Re-running with the same seed gives byte-identical files.
**Verify:** `make data` twice, diff outputs; manually spot-check 50 random pairs.
**Size:** M

### T1b. Handcrafted benchmark (parallel with T2–T6)
**Do:** `data/handcrafted/benchmark.csv` with 30–50 hand-labelled lines from Kafka, Redis, OpenSearch, Docker, Kubernetes (kubelet), PostgreSQL, Nginx, following Loghub conventions. Cover: multi-variable lines, paths/URLs, JSON-in-log, stack-trace headers, constant numbers (e.g. `HTTP/1.1`), no-variable lines.
**Accept:**
- [ ] ≥30 lines, each edge-case category above has ≥2 lines.
- [ ] Never used for tuning or training.
- [ ] Same CSV schema as the Loghub data (`system, content, gold`).
**Verify:** load through the T2 evaluator without schema errors.
**Size:** S (manual effort, not code)

### T2. Evaluation harness and Drain baseline (B0)
**Do:** `src/evaluate.py` wraps the logpai evaluator → GA / FGA / PA / FTA per system and average, writes `results/<model>/<split>.json`. `src/baselines/drain_baseline.py` runs `logparser3` Drain on the test splits.
**Accept:**
- [ ] Feeding gold as predictions returns PA = 1.0 on every split (sanity check).
- [ ] The identical `post_process` runs on gold and predictions.
- [ ] Drain results exist for held-out and template-disjoint splits, produced by your own run (not literature numbers).
**Verify:** unit test for the gold-equals-pred case; `make baselines` produces the JSON.
**Size:** M

### T3. predict.py with `parse_lines`
**Do:** `src/predict.py`: `parse_lines(lines: list[str], system: str | None, backend: str, model: str, adapter: str | None) -> list[str]` plus a CLI (`--backend vllm|ollama`, `--split`, `--out`). Greedy decoding, shared prompt builder, output cleanup (first line only, strip quotes/backticks, count how often cleanup was needed). CLI writes CSV `system, content, gold, pred`. vLLM backend uses `enable_lora`; Ollama backend calls the local HTTP API.
**Accept:**
- [ ] `parse_lines` has no dependency on split files or the evaluator (importable by Phase B).
- [ ] Both backends return the same-length list as the input, in order.
- [ ] Cleanup-needed rate is logged per run.
- [ ] Ollama backend is smoke-tested on one line; the vLLM backend on a 200-line batch on the T4.
**Verify:** small test with a stub backend for order and length; run both real backends once.
**Size:** M

### T4. Base-model baselines (B1 zero-shot, B2 few-shot)
**Do:** `src/baselines/prompt_baseline.py` (or flags on `predict.py`) builds the zero-shot prompt and a 5-example few-shot prompt, using the identical system prompt as fine-tuning. Run on held-out, template-disjoint and handcrafted sets.
**Accept:**
- [ ] B1 and B2 results in `results/` for all three test sets.
- [ ] Few-shot examples come from training systems only.
- [ ] Base-model cleanup rate recorded (it is itself a finding).
**Verify:** `make baselines`; spot-check 20 predictions for `<think>` blocks (must not appear with Instruct-2507).
**Size:** S

**Checkpoint 1 (after T4):** pipeline works end to end for baselines only. B0, B1 and B2 numbers exist on the same splits. Review: are the baseline numbers plausible (Drain PA low, base model chatty)? If not, fix the harness before training.

### T5. train.py and smoke run
**Do:** `src/train.py` driven by one YAML (guide §8 config): Unsloth + TRL `SFTTrainer`, 4-bit, `train_on_responses_only`, fp16, checkpoints to Drive with resume, early stopping on **validation PA** (custom callback generating on ~200 val lines), W&B logging of config, loss, val PA, peak GPU memory, wall time. Smoke run: 20 steps on a tiny subset.
**Accept:**
- [ ] Smoke run finishes on the T4, writes a checkpoint to Drive, and logs to W&B.
- [ ] Kill the run mid-way; re-launching resumes from the last checkpoint.
- [ ] Peak VRAM under 12 GB at `max_seq_length=512`.
- [ ] Loss is computed on the response only (verify by decoding the labels of one batch).
**Verify:** run on Colab; inspect the W&B run; decode one batch's labels.
**Size:** L

### T6. First full run and comparison
**Do:** Train `configs/qwen3_4b_r16.yaml` on the full train split. Evaluate on held-out and template-disjoint with `predict.py` + `evaluate.py`.
**Accept:**
- [ ] Run finishes in under ~1 h on the T4.
- [ ] PA on held-out systems is reported next to B0, B1, B2 in one table.
- [ ] If fine-tuned PA does not beat B2, stop and diagnose (data, prompt, masking) before the sweep.
**Verify:** results table in `results/summary.md`.
**Size:** M

### T7. One-axis-at-a-time sweep
**Do:** `configs/sweep.yaml`. Vary rank (8/16/32), LR (1e-4/2e-4/5e-4), epochs (1/3/5), target modules (`q,v` vs all-linear), and optionally the `System:` line on/off. Tune on validation only; never the held-out systems. About 10 runs, then one confirmation run of the best combination.
**Accept:**
- [ ] `reports/sweep.md` exported from W&B, with the winner and why.
- [ ] Held-out systems untouched (assert in code that sweep configs read only train/val).
- [ ] Best config saved as `configs/best.yaml`.
**Verify:** compare runs in W&B; confirm the best config beats T6 on validation PA.
**Size:** L

### T8. Final evaluation suite
**Do:** Evaluate the best checkpoint plus B0–B2 on: held-out systems, template-disjoint, handcrafted set, and a 5–10k-line stress sample from Loghub-2.0 (held-out systems). Build the per-system table, "fixed" and "broke" line lists, and the error taxonomy (over-generalized / under-generalized / format / hallucinated) in `notebooks/10_error_analysis.ipynb`.
**Accept:**
- [ ] All results written to `results/<model>/<split>.json`.
- [ ] Taxonomy counts cover every wrong prediction (rule-based labeling; LLM judge optional).
- [ ] Stress sample is generated by a seeded script, not by hand.
**Verify:** `make eval` regenerates every table from the saved predictions.
**Size:** M

### T9. Forgetting check
**Do:** lm-eval-harness (`hellaswag`, `arc_easy`, `ifeval`, `--limit 200`) on base vs fine-tuned.
**Accept:**
- [ ] % retained per task reported. If the drop is significant, document the trade-off and test a lower rank or fewer epochs.
**Size:** S

### T10. Model-size table
**Do:** Run `best.yaml` on Llama 3.2 3B and Gemma 3 1B (8B only if time allows). Table: PA vs params vs tokens/sec.
**Accept:**
- [ ] Same data, prompt and metric as the primary model.
- [ ] Template and tokenizer quirks noted in `reports/`.
**Size:** M

### T11. Export
**Do:** Save the LoRA adapter, push to the HF Hub with a model card, and export merged GGUF Q4_K_M. Verify through Ollama on the laptop (CPU only).
**Accept:**
- [ ] GGUF loads in Ollama and `predict.py --backend ollama` reproduces vLLM PA on the 200-line check within ~1–2 points (quantization drift measured and reported).
- [ ] Adapter is under ~100 MB; the model card cites LogPAI and Loghub-2.0.
**Verify:** run the held-out set through both backends and compare.
**Size:** M

### T12. Phase A report
**Do:** `reports/REPORT.md`: problem, why fine-tune over prompting (B2), data card, leakage prevention, sweep, head-to-head, error taxonomy, forgetting, model size, limitations.
**Accept:**
- [ ] Every number in the report traces to a file in `results/`.
- [ ] README cites LogPAI and Loghub-2.0.
**Size:** M

**Checkpoint A (end of Phase A):**
- [ ] Fine-tuned model beats B0, B1, B2 on held-out PA, or the report explains honestly why not.
- [ ] No hybrid code exists in Phase A files.
- [ ] `make data train eval baselines` reproduces the results from a clean checkout.
- [ ] Human review before starting Phase B.

---

## Phase B: Hybrid pipeline (`src/pipeline/`)

Each Phase B task lives in its own module and calls the model only through `predict.parse_lines`. Phase B must not change Phase A files or results.

### B1. Pre-parser
**Do:** `src/pipeline/preparse.py`: per-format header stripping (Kafka, Kubernetes, Nginx, PostgreSQL, Redis, OpenSearch), message extraction from JSON logs, folding multi-line stack traces into one logical entry. Returns `(header, message)` per entry.
**Accept:**
- [ ] One test fixture of ≥10 lines per format; message extraction is exact.
- [ ] A stack trace of N lines becomes 1 entry.
- [ ] Unknown-format lines pass through unchanged (never dropped).
**Size:** M

### B2. Drain grouping + LLM on samples
**Do:** `src/pipeline/group.py`: Drain-group the messages, pick 2–3 sample lines per group, call `parse_lines`, and keep a group→template mapping.
**Accept:**
- [ ] LLM calls = groups × samples, counted and logged.
- [ ] If the samples yield different templates, the pipeline picks one deterministically (documented rule).
**Size:** M

### B3. Regex validation and fallback
**Do:** `src/pipeline/validate.py`: compile each template to a regex (`<*>` → a non-greedy wildcard), match it against every line in the group, and re-parse non-matching lines individually.
**Accept:**
- [ ] Regex escaping handles special characters in templates (test with `[`, `(`, `.`, `*`).
- [ ] Every input line ends with a template that matches it, or is flagged `unparsed`.
- [ ] Fallback call count is logged.
**Verify:** test with a deliberately wrong template; confirm the fallback fires.
**Size:** M

### B4. Template cache
**Do:** `src/pipeline/cache.py`: persistent template store (a JSONL or SQLite file for now) keyed so that a repeated line shape skips the LLM. The interface must be swappable for Redis in Phase C.
**Accept:**
- [ ] A second run over the same file makes ~0 LLM calls.
- [ ] Cache hit rate reported.
- [ ] Interface is `get(key)` / `put(key, template)` only.
**Size:** S

### B5. Batch CLI
**Do:** `python -m src.pipeline.run --input file.log --format kafka --backend ollama` → `templates.jsonl` (template, count, example) plus a per-line template assignment file.
**Accept:**
- [ ] Runs on the laptop via Ollama (CPU) and on the server via vLLM, with no code changes.
- [ ] A 100k-line file completes and reports lines/sec.
**Size:** M

### B6. System-level evaluation
**Do:** `src/pipeline/eval_system.py`: end-to-end accuracy (the same logpai metrics) on Loghub-2.0 samples, plus lines/sec, LLM calls per 1M lines, cache hit rate. Compare against model-only per-line parsing and Drain. Also run on a sample of your own service logs.
**Accept:**
- [ ] Results in `results/pipeline/`.
- [ ] Reports whether the hybrid improves PA, cuts LLM calls, or both.
- [ ] Own-log run labelled qualitatively; a spot-check of 50 templates is recorded.
**Size:** M

### B7. Packaging and docs
**Do:** `docker-compose.yml` (Ollama + pipeline), `Makefile` targets (`make pipeline`), README usage, `reports/PIPELINE.md`.
**Accept:**
- [ ] `docker compose up` parses a sample file on a GPU-less laptop.
**Size:** S

**Checkpoint B (end of Phase B):**
- [ ] System-level metrics are reported for all four measures (accuracy, lines/sec, LLM calls per 1M lines, cache hit rate).
- [ ] Pipeline runs on laptop (Ollama) and server (vLLM) unchanged.
- [ ] Human review before any streaming work.

---

## Phase C: Streaming (placeholder, not planned in detail)

Kafka consumer workers + Redis-backed template store behind the B4 interface. Plan it after Checkpoint B using the measured throughput.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Colab session dies mid-run | Lost training | Checkpoints to Drive, resume, runs under ~1 h, Kaggle as backup |
| Unsloth / TRL / vLLM API drift | Broken installs | Pin versions at T0, fall back to plain PEFT + TRL |
| Template leakage inflates PA | Fake results | Assertion in T1; held-out systems never touched in T7 |
| Fine-tune does not beat few-shot (B2) | No story | Stop at T6, diagnose before the sweep |
| GGUF quantization drops PA | Laptop use worse than the reported numbers | Measure drift in T11, report both numbers |
| Own-log formats not covered by pre-parser | Poor real-world results | Unknown-format passthrough (B1), per-format fixtures |
| CPU speed in Ollama too slow for millions of lines | Impractical for large files | Hybrid grouping + cache cut LLM calls (B2–B4); heavy batches go to the server via vLLM |

## Open questions

- Which model for the pipeline default if the 3B or 1B is within ~2 PA points of the 4B? A smaller model would be much faster on CPU. Decide after T10.
- Cache key design (raw message vs masked shape) affects hit rate. Decide in B4 after looking at real data.
