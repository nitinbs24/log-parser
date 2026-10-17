# LoRA Fine-Tuning for Log Parsing on Google Colab

**Goal:** Fine-tune a small open-source LLM with LoRA to convert raw system log lines into log templates. Evaluate it against the base model and against classic parsers (Drain) on public Loghub data. Do the entire thing on Google Colab's T4 GPU.

> Adapted from the BASWE "Fine-Tuning Pipeline with LoRA" guide. Every phase of that guide is kept, but the dataset phase shrinks from "build a dataset" to "reshape an existing labelled one", and everything is sized for a 15 GB T4.

---

## 1. The task, explained

### What log parsing is

Software emits logs from `printf`-style statements. Every line is a **fixed template** filled with **variables**:

```
Raw:      Received block blk_-562725280853087685 of size 67108864 from /10.251.91.84
Template: Received block <*> of size <*> from <*>
```

**Log parsing** means recovering the template, and therefore the variables, from the raw line. You get no access to the source code. It is the first step of nearly every downstream log-analytics task:

- **Anomaly detection.** Templates become event IDs, and you model sequences of event IDs.
- **Log compression and search.** You store each template once and keep only the variables per line.
- **Alert grouping and root-cause analysis.** A thousand lines collapse into twelve event types.

### Why it's a good fine-tuning task

| Property | Why it matters for this project |
|---|---|
| **Exact ground truth** | Each line has one correct template, so you can measure exact-match accuracy with no judge needed. |
| **Base models are bad at it** | They over-generalize ("make everything `<*>`"), under-generalize (they leave IDs in), invent placeholder styles (`{id}`, `[IP]`), or add chatty text around the answer. |
| **Fine-tuning visibly fixes it** | The model learns the convention: what counts as a variable, the `<*>` syntax, and output-only formatting. |
| **Strong classical baseline** | You can compare against Drain, a non-ML parser. You beat a real tool, not just a weak LLM. |
| **Short sequences** | Log lines are tens of tokens. Training is fast and cheap on a T4, and a full hyperparameter sweep is realistic. |
| **Story fit** | It connects directly to distributed-systems work (Kafka, Kubernetes, HDFS, Spark logs). |

### Where it's hard (the stuff you'll write about in the report)

- **Ambiguous tokens.** `true`, `ERROR`, or a hostname can be a constant in one template and a variable in another.
- **Unseen systems.** A parser trained on HDFS logs must handle OpenSSH logs it has never seen. This cross-system generalization is the real test.
- **Consistency.** The same template must be produced for every line of an event type. One stray token difference breaks grouping metrics.

---

## 2. Datasets

All datasets come from **LogPAI** and are free for research use (cite the papers).

| Dataset | Size | Use it for |
|---|---|---|
| **Loghub-2k** (`2k_dataset/` in the `logpai/loghub-2.0` repo) | 16 systems × 2,000 labelled lines each | **Training and main evaluation.** Small enough to iterate on Colab. |
| **Loghub-2.0** (full, from Zenodo record 8275861, ~1 GB zipped) | 14 systems, ~3.6M labelled lines per system on average | **Stress test.** Sample ~5–10k lines from held-out systems. Do not run all of it on a T4. |
| **Loghub** (raw, `logpai/loghub`) | 19 systems, unlabelled | Optional extra unlabelled lines for qualitative demos. |

Systems covered include HDFS, Hadoop, Spark, Zookeeper, OpenStack, BGL, HPC, Thunderbird, Linux, Mac, Windows, Android, HealthApp, Apache, OpenSSH and Proxifier. Loghub-2.0 drops Windows and Android.

**Use the `Content` column, not the full raw line.** The structured CSVs already split off the header (timestamp, level, component). Every published parser parses `Content` → `EventTemplate`. Follow that convention, or your numbers won't be comparable.

---

## 3. Evaluation metrics (the four standard ones)

| Metric | Level | Measures | Notes |
|---|---|---|---|
| **GA**: Grouping Accuracy | Message | Fraction of lines placed in exactly the right group | Inflated by frequent templates |
| **FGA**: F1 of Grouping Accuracy | Template | F1 over templates whose group is exactly right | Introduced with Loghub-2.0 to fix GA's frequency bias |
| **PA**: Parsing Accuracy | Message | Fraction of lines whose predicted template is an exact match | **Your headline metric.** It's what generation actually controls. |
| **FTA**: F1 of Template Accuracy | Template | F1 over templates that are both correctly grouped and exactly correct | The strictest metric |

For an LLM parser, "groups" = lines that received the identical predicted template string. GA and FGA therefore fall out of the generations for free.

**Don't implement these yourself.** Reuse the evaluator and the template `post_process` normalization from the `logpai/loghub-2.0` repo. Run it on predictions *and* ground truth, so `<*> <*>` vs `<*>` style differences don't count as errors.

---

## 4. Baseline numbers from the literature

Use these numbers to position your result. **Do not compare your Loghub-2k numbers directly to Loghub-2.0 numbers.** The two benchmarks give materially different scores. Run Drain yourself on your exact test split, and cite these only as context.

| Method | Type | Benchmark | GA | PA | FGA | FTA |
|---|---|---|---|---|---|---|
| **Drain** (2017) | Statistic (tree-based) | Loghub-2.0 avg | 0.840 | 0.470 | ~0.55 | n/a |
| **LogPPT** (2023) | Prompt-tuned RoBERTa | Loghub-2.0 avg | 0.560 | n/a | n/a | n/a |
| **LibreLog** (2024) | Unsupervised, Llama 3 8B + grouping + RAG | Loghub-2.0 | 0.872 | 0.854 | 0.823 | 0.651 |
| **PIPLUP** (2025) | Statistic, configuration-free | Loghub-2.0 | 0.931 | 0.781 | 0.857 | 0.557 |
| **LILAC** (2024) | GPT-3.5 in-context learning + parsing cache | Paper headline | n/a | 0.842 | n/a | 0.810 |
| **LLMParser** (ICSE 2024) | **Fine-tuned** Flan-T5 / LLaMA-7B, 50 shots per system | Loghub-2k, 16 systems | n/a | ~0.96 avg | n/a | n/a |

### What these tell you

1. **Drain is the bar to clear on PA.** It groups well (high GA) but writes poor templates (PA ≈ 0.47 on Loghub-2.0). An LLM wins exactly where Drain loses.
2. **LLMParser is your closest prior work.** It fine-tuned LLMs on per-system samples and hit ~96% PA. Read it before you start. Its most interesting finding is that **Flan-T5-base performed comparably to LLaMA-7B**, so a small model can be enough.
3. **Your differentiator vs LLMParser** should be **cross-system generalization**. Train on some systems and test on systems the model has never seen. LLMParser trained per system. "My adapter parses logs from systems it never saw" is a stronger and more realistic claim.

### Your own baselines to run (mandatory)

| # | Baseline | What it shows |
|---|---|---|
| B0 | **Drain** (`logpai/logparser`, also on PyPI as `logparser3`) on the same test split | Classic non-ML tool |
| B1 | **Base model, zero-shot** with your exact prompt | The denominator for every "improvement" claim |
| B2 | **Base model, few-shot** (5 in-context examples) | Answers "why not just prompt it?" This is the interview question you must pre-empt. |
| B3 | **Fine-tuned model** (your best checkpoint) | The result |
| B4 *(optional)* | **Fine-tuned Flan-T5-base** | Replicates LLMParser's small-model finding on your split |

---

## 5. Hardware: what your Colab options actually mean

From your runtime picker, you have **CPU, T4 GPU, and v5e-1 TPU** available. The others are greyed out.

| Option | Verdict | Why |
|---|---|---|
| **T4 GPU** (16 GB, ~15 GB usable) | ✅ **Use this** | Supported by Unsloth, bitsandbytes (4-bit QLoRA) and vLLM. Plenty for 1–4B models, and an 8B model fits in 4-bit with short sequences. |
| **v5e-1 TPU** | ❌ Skip | bitsandbytes, Unsloth and most PEFT/QLoRA tooling are CUDA-only. You'd have to rewrite in JAX/Keras for no gain at this scale. |
| **CPU** | Only for data prep, Drain baseline, and evaluation scoring | Drain runs on CPU anyway. |

### T4 quirks you must plan around

- **No bfloat16.** The T4 is compute capability 7.5. Use `fp16=True` and `bf16=False`. Unsloth's `is_bfloat16_supported()` handles this automatically.
- **No FlashAttention 2.** That's fine, since Unsloth uses its own kernels and your sequences are short.
- **Sessions die.** Free sessions disconnect on idle and have hard time caps, and GPU access is quota-limited and varies. Mitigations:
  - Mount Google Drive and write `output_dir` and checkpoints there.
  - Set `save_steps` small (~every 50–100 steps) and use `resume_from_checkpoint=True`.
  - Log to **W&B**, so curves survive a crash.
  - Keep each run under ~1 hour. With ~1.5k short examples, a 3–4B model trains in well under that.
- **Backup GPU:** Kaggle notebooks give a weekly free GPU quota (T4 ×2 or P100). The same code runs there if Colab throttles you.

---

## 6. Model selection

### Candidates that fit a T4

| Model | Params | 4-bit VRAM for training* | Pros | Cons | Role |
|---|---|---|---|---|---|
| **Qwen3-4B-Instruct-2507** | 4B | ~5–7 GB | Strong at structured output, great Unsloth support, fast sweeps | Thinking/non-thinking template quirks; use the Instruct-2507 variant | ⭐ **Primary** |
| **Llama 3.2 3B Instruct** | 3B | ~4–6 GB | Very well documented, clean chat template | Slightly weaker baseline, which means a bigger visible gain (fine for the story) | Strong alternative |
| **Gemma 3 4B / 1B** | 1–4B | ~3–7 GB | Gemma 3 1B is tiny, so it makes a great "how small can we go" data point | Template and attention quirks; check Unsloth notes | Ablation |
| **Llama 3.1 8B / Qwen3-8B** | 8B | ~11–14 GB | Matches the BASWE guide's "8B" suggestion | Tight on a T4, a slow sweep, and you'll hit session limits | One final run only, if at all |
| **Flan-T5-base** | 250M | <2 GB, no quantization needed | LLMParser's surprise winner; super fast | Encoder-decoder, so a different training code path | Optional baseline B4 |

\* Rough, at `max_seq_length=512`, batch size ~8. Logs are short, which keeps memory low.

**Recommendation:** Do the whole pipeline and the sweep on **Qwen3-4B-Instruct-2507**. Then run the single best config on **Llama 3.2 3B** and **Gemma 3 1B** for a model-size table.

The headline you're after: *"A fine-tuned 4B model beats Drain and its own 8B big brother on unseen systems."*

> Models move fast. If Unsloth's catalog has a newer small Qwen/Gemma/Llama generation when you start, swap it in. Nothing in this pipeline is model-specific beyond the chat template.

---

## 7. Tech stack (with comparisons)

### 7.1 Fine-tuning framework

| Option | Speed/VRAM on T4 | Learning value | Effort | Verdict |
|---|---|---|---|---|
| **Unsloth** (wraps HF TRL/PEFT) | Best: ~2× faster, much lower VRAM | Good. It's still `SFTTrainer` and `LoraConfig` underneath. | Low; Colab notebooks exist | ⭐ **Use** |
| **Plain HF PEFT + TRL + bitsandbytes** | Baseline | Highest; you see every knob | Medium | Use if Unsloth breaks on a model |
| **Axolotl** | Good | Config-driven (YAML), less code | Medium; heavier install on Colab | Skip for now |
| **LLaMA-Factory** | Good | Web UI / YAML, hides internals | Low | Skip, since it hides too much for a portfolio project |

Unsloth also gives you `train_on_responses_only`, which computes loss only on the template, not the prompt. **Use it.** With short targets, prompt tokens would otherwise dominate the loss.

### 7.2 Experiment tracking

| Option | On Colab | Verdict |
|---|---|---|
| **Weights & Biases** | Hosted, so it survives disconnects. Free for personal use, with a sweep feature built in. | ⭐ **Use** |
| **MLflow** | Needs a tracking server. On Colab that's local files on Drive or a tunnel. Better for self-hosted/production narratives. | Use only if you specifically want "self-hosted MLOps" on your resume |

### 7.3 Evaluation

| Component | Tool |
|---|---|
| Task metrics (GA/FGA/PA/FTA) | Evaluator + `post_process` from `logpai/loghub-2.0` |
| Batch inference for eval | **vLLM** on the T4 (fp16, `enable_lora=True`). It's much faster than HF `generate` over thousands of lines. |
| Forgetting check | **lm-evaluation-harness**: `hellaswag`, `arc_easy`, `ifeval` with `--limit 200` to keep it T4-friendly |
| Error analysis / judge | Optional LLM-as-judge (any strong API model) only to **categorize errors** (over-generalized, missed variable, format). Correctness itself is exact-match. |

### 7.4 Serving / demo

| Option | Where | Multi-LoRA | Verdict |
|---|---|---|---|
| **vLLM** | Colab T4 (or any CUDA box) | Yes. Base + adapter served side by side; pick per request via `model` name. | ⭐ **Use for the A/B endpoint and throughput benchmarks** |
| **Ollama** (GGUF) | Your laptop, CPU is fine for 3–4B Q4 | One model per tag (merge the adapter first) | ⭐ **Use for a local, always-available demo** |
| **llama.cpp server** | Laptop | Supports LoRA adapters on GGUF | Alternative to Ollama with more control |
| **HF TGI** | GPU server | Yes | Overkill here |

Unsloth exports directly to GGUF (`save_pretrained_gguf`), so the Ollama path is about three lines of code.

### 7.5 Final stack

```
Python 3.11 · Unsloth (TRL SFTTrainer + PEFT LoRA, bitsandbytes 4-bit)
Qwen3-4B-Instruct-2507 (primary) · Llama 3.2 3B · Gemma 3 1B (ablations)
Loghub-2k (train/eval) · Loghub-2.0 sample (stress test)
W&B (tracking + sweeps) · logpai evaluator · Drain (logparser3) · lm-eval-harness
vLLM (batch eval + A/B API) · FastAPI (A/B endpoint) · Ollama/GGUF (local demo)
Docker Compose (inference + API) · GitHub repo with configs
```

---

## 8. Project build plan

Timeline follows the BASWE guide's 14 days. The data phase is shorter because the labels already exist, and that time moves into evaluation and the cross-system study, which is where this project stands out.

### Phase 0: Setup (Day 1)

1. Create the repo (layout in §9). Add `configs/`, `src/`, and `notebooks/`.
2. Write a Colab bootstrap notebook that:
   - mounts Drive,
   - `git clone`s your repo,
   - installs pinned versions of `unsloth`, `trl`, `peft`, `vllm`, `wandb`, `logparser3`,
   - logs in to W&B and HF.
3. Clone `logpai/loghub-2.0`, and copy `2k_dataset/` and the evaluator into a `third_party/` folder.
4. Sanity check: load Qwen3-4B in 4-bit on the T4 and generate one response.

### Phase 1: Dataset (Days 1–3)

**Step 1. Choose the split strategy.** This is the most important design decision in the project.

Log data leaks easily. Thousands of lines share one template, so a random line-level split puts the same template in train and test, and your accuracy will be fake.

| Split | Train | Test | Purpose |
|---|---|---|---|
| **Cross-system (primary)** | 12 systems | 4 **held-out systems**, e.g. one each from distributed/supercomputer/OS/app: `OpenStack`, `Thunderbird`, `Mac`, `Proxifier` | "Works on logs it's never seen": your headline |
| **In-system, template-disjoint (secondary)** | ~70% of templates per training system | The other ~30% of templates | Generalization to new events in known systems |
| **Validation** | Carved from the training systems, template-disjoint | n/a | Early stopping and the sweep. **Never** use the held-out systems. |

Fix the held-out systems in `configs/split.yaml` with a seed, and never touch them during tuning.

**Step 2. Build the training examples.**

- Dedupe on `(system, Content)`.
- **Cap examples per template** (e.g. ≤3). Frequent templates would otherwise drown out rare ones, and rare templates are where models fail.
- Target **~1,000–2,000 training examples**, in line with the BASWE guide's range.

Use a chat format with completion-only loss:

```json
{"messages": [
  {"role": "system", "content": "You are a log parser. Replace every variable in the log message with <*>. Output only the template."},
  {"role": "user", "content": "System: HDFS\nLog: Received block blk_-562725280853087685 of size 67108864 from /10.251.91.84"},
  {"role": "assistant", "content": "Received block <*> of size <*> from <*>"}
]}
```

Ablation idea: include vs. exclude the `System:` line. Does the system name help or cause overfitting? It's a cheap, interesting result.

**Step 3. Clean the data.**

- Apply the repo's template `post_process` to targets.
- Drop lines over ~400 tokens.
- Spot-check 50 random pairs by eye.

**Step 4. Build your handcrafted benchmark (30–50 lines).** This is the "sacred" set the BASWE guide asks for, and it's where you inject your own value.

- Pull logs from systems you've actually run: **Kafka, Redis, OpenSearch, Docker, Kubernetes (kubelet), PostgreSQL, Nginx**.
- Label templates by hand following Loghub conventions.
- Cover edge cases on purpose:
  - multi-variable lines,
  - paths and URLs,
  - JSON-in-log lines,
  - stack-trace headers,
  - numbers that are constants (e.g. "HTTP/1.1"),
  - lines with **no** variables.

Fully out-of-distribution data you labelled yourself is a strong talking point.

**Step 5. Write dataset stats to `reports/data_card.md`.** Include lines and templates per system, per split, the length distribution, and the template-frequency skew.

### Phase 2: Training pipeline (Days 4–6)

**1. Write `src/train.py`, driven entirely by a YAML config**, so every run is reproducible from its config.

```yaml
model: unsloth/Qwen3-4B-Instruct-2507-bnb-4bit
max_seq_length: 512
load_in_4bit: true
lora:
  r: 16
  alpha: 32          # 2x rank
  dropout: 0.05      # Unsloth's fast path prefers 0; test both
  target_modules: [q_proj, v_proj]   # BASWE baseline; ablate vs all-linear
train:
  lr: 2.0e-4
  epochs: 3
  per_device_batch_size: 8
  grad_accum: 2
  warmup_ratio: 0.05
  scheduler: cosine
  fp16: true
  bf16: false
  eval_steps: 50
  save_steps: 50
  early_stopping_patience: 3
  seed: 42
output_dir: /content/drive/MyDrive/logparse/runs/${run_name}
```

**2. Log everything to W&B:**

- the full config,
- loss and validation loss,
- **validation PA** (run a fast generation on ~200 validation lines at each eval step, via a custom callback),
- GPU memory (`torch.cuda.max_memory_allocated`),
- wall time.

**3. Use early stopping on validation PA, not validation loss.** Loss can keep falling while exact-match plateaus. Log which checkpoint won and why.

**4. Run the sweep on the T4, keeping each run short.**

| Axis | Values |
|---|---|
| Rank | 8, 16, 32 |
| Learning rate | 1e-4, 2e-4, 5e-4 |
| Epochs | 1, 3, 5 (or rely on early stopping) |
| Target modules | `q,v` vs all linear layers |

Don't run the full grid (54 runs). Fix the defaults, vary **one axis at a time** (~10 runs), then confirm the best combo. Export the W&B comparison table to `reports/sweep.md`.

### Phase 3: Evaluation (Days 7–10)

1. **Write `src/predict.py`.** vLLM batch inference with greedy decoding (`temperature=0`, `max_tokens=128`), and the same prompt for every model. Save predictions as CSV with columns `system, content, gold, pred`.
2. **Write `src/evaluate.py`.** Run the logpai evaluator → GA/FGA/PA/FTA per system plus the averages. Write the results to `results/<model>/<split>.json`.
3. **Run all baselines (B0–B4) on:**
   - the 4 held-out systems (Loghub-2k),
   - the template-disjoint in-system test,
   - your handcrafted 30–50 set,
   - **a stress test**: 5–10k lines sampled from the Loghub-2.0 full data of the held-out systems.
4. **Do a head-to-head analysis.**
   - Per-system table.
   - Lists of lines that **fine-tuning fixed** and lines that **it broke** (regressions).
   - An error taxonomy:
     - over-generalized (a constant was replaced with `<*>`),
     - under-generalized (a variable was kept),
     - format violation,
     - hallucinated text.
   - Optional: an LLM judge to auto-label the error categories.
5. **Check for catastrophic forgetting.** Run lm-eval-harness (`hellaswag`, `arc_easy`, `ifeval`, `--limit 200`) on base vs. fine-tuned. Report the % retained. If the drop is significant, try lower rank or fewer epochs, and document the trade-off.
6. **Run the model-size table.** Run the best config on Llama 3.2 3B and Gemma 3 1B (and optionally 8B), and plot PA vs. params vs. tokens/sec.

### Phase 4: Inference pipeline (Days 10–12)

1. **Package the adapter.** Save the LoRA adapter only (tens of MB) and push it to the HF Hub with a model card. Also export a **merged GGUF (Q4_K_M)** for Ollama.
2. **Serve with vLLM.**

   ```
   vllm serve Qwen/Qwen3-4B-Instruct-2507 --enable-lora \
     --lora-modules logparser=<path-or-hf-id> --dtype half --max-model-len 1024
   ```

   Benchmark tokens/sec, P50/P95 latency, and max concurrency (e.g. with `vllm bench` or a small `locust`/`asyncio` script).
3. **Build the A/B endpoint** in FastAPI: `POST /parse {"log": "..."}` returns `{base, finetuned, drain}`. Include Drain in the response too; seeing all three side by side makes a great demo. On Colab, expose it temporarily through a tunnel (`cloudflared`). Locally, point it at Ollama.
4. **Batch mode (stretch goal):** `POST /parse_file` takes a log file and returns template groups with counts. This is the "real tool" version.

### Phase 5: Containerize and document (Days 12–13)

1. Write a `docker-compose.yml` with two services:
   - Ollama (fine-tuned GGUF + base model),
   - FastAPI A/B service.

   It should run on your laptop with no GPU.
2. Add `make` targets (or a `justfile`):

   ```
   make data       # raw Loghub -> splits + jsonl
   make train      CONFIG=configs/qwen3_4b_r16.yaml
   make eval       MODEL=... SPLIT=heldout
   make baselines  # drain + base zero/few-shot
   make serve
   ```

3. Write the experiment report (`reports/REPORT.md`). Cover:
   - problem framing,
   - **why fine-tuning over prompting or RAG** (point to B2),
   - the data card,
   - split methodology and leakage prevention,
   - sweep results,
   - head-to-head tables,
   - error taxonomy with examples,
   - the forgetting analysis,
   - the model-size trade-offs,
   - limitations.

### Phase 6: Portfolio polish (Days 13–14)

1. **Record a demo under 4 minutes.** Paste a gnarly Kubernetes or Kafka log line. Show the base model mangling it, Drain getting the grouping right but the template wrong, and the fine-tuned model nailing it. Then show the W&B curves and the per-system results table.
2. **Write the headline**, with every number backed by `results/`:

   > *"Fine-tuned Qwen3-4B with LoRA on ~1.5k log/template pairs from 12 Loghub systems. On 4 systems never seen in training, parsing accuracy rose from X% (base) to Y%, beating Drain (Z%) on the same split, while retaining W% of general benchmark performance. Trained entirely on a free Colab T4."*

---

## 9. Repo layout

```
log-parser-lora/
├── configs/
│   ├── split.yaml                 # held-out systems, seed, per-template cap
│   ├── qwen3_4b_r16.yaml          # one file per run
│   └── sweep.yaml                 # W&B sweep definition
├── data/
│   ├── raw/                       # Loghub-2k CSVs (gitignored, fetched by script)
│   ├── processed/                 # train/val/test jsonl
│   └── handcrafted/benchmark.csv  # your 30–50 labelled lines (committed)
├── src/
│   ├── prepare_data.py
│   ├── train.py
│   ├── predict.py                 # vLLM / HF backends
│   ├── evaluate.py                # wraps logpai evaluator
│   ├── baselines/drain_baseline.py
│   ├── baselines/prompt_baseline.py   # zero/few-shot base model
│   └── serve/app.py               # FastAPI A/B endpoint
├── third_party/loghub2_eval/      # vendored evaluator + post_process (with license/cite)
├── notebooks/
│   ├── 00_colab_bootstrap.ipynb
│   └── 10_error_analysis.ipynb
├── results/                       # json metrics per model/split (committed)
├── reports/  data_card.md · sweep.md · REPORT.md
├── docker-compose.yml · Makefile · README.md
```

---

## 10. Gotchas checklist

- [ ] **Template leakage.** Split by template or system, never by line. Assert in code that no test template string appears in the training targets.
- [ ] **Same prompt for base and fine-tuned.** Otherwise your comparison is invalid.
- [ ] **Normalize before scoring.** Run the identical `post_process` on gold and predictions.
- [ ] **Strip model chatter.** Take the first line of the output, and strip quotes and backticks. Report how often stripping was needed for the base model; that number is itself a finding.
- [ ] **Qwen3 thinking mode.** Use the Instruct-2507 (non-thinking) variant, or disable thinking in the chat template, so you don't get `<think>` blocks.
- [ ] **fp16 on T4.** A `bf16=True` left over from an A100 tutorial will crash.
- [ ] **Checkpoints to Drive**, not `/content`. Everything in `/content` vanishes on disconnect.
- [ ] **Pin versions.** Unsloth/TRL/vLLM APIs move fast; pin them in `requirements.txt` the day it works.
- [ ] **Don't compare across benchmarks.** Literature numbers on Loghub-2.0 are not comparable to your Loghub-2k split. Your own Drain run is the fair comparison.
- [ ] **Cite LogPAI and Loghub-2.0** in the README (it's a condition of dataset use).

---

## 11. Stretch goals (if you finish early)

1. **Hybrid parser.** Use Drain to group lines, then call the fine-tuned LLM once per group, and cache by template. This is how LILAC/LibreLog get production-level throughput; benchmark lines/sec before and after.
2. **Variable extraction.** Output JSON `{template, variables: [...]}` and score variable-level F1.
3. **Downstream payoff.** Feed your templates into a simple HDFS anomaly detector (HDFS has block-level anomaly labels). Show that better parsing leads to better detection. This closes the loop from "parsing" to "why anyone cares".
4. **Online demo.** Pipe `docker logs -f` or `kubectl logs -f` through the API and show live template grouping.
5. **Second adapter.** Later, train your shorts-script adapter on the same base model and serve both from one vLLM instance with multi-LoRA. This demonstrates the adapter-swapping point from the BASWE guide.

---

## 12. Key references

- Jiang et al., *A Large-Scale Evaluation for Log Parsing Techniques: How Far Are We?* (ISSTA 2024): Loghub-2.0, FGA metric. arXiv:2308.10828 · github.com/logpai/loghub-2.0
- Zhu et al., *Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics* (ISSRE 2023). github.com/logpai/loghub
- Ma et al., *LLMParser: An Exploratory Study on Using Large Language Models for Log Parsing* (ICSE 2024). arXiv:2404.18001 · github.com/zeyang919/llmparser
- Jiang et al., *LILAC: Log Parsing using LLMs with Adaptive Parsing Cache* (FSE 2024). arXiv:2310.01796
- Ma et al., *LibreLog: Accurate and Efficient Unsupervised Log Parsing Using Open-Source LLMs*. arXiv:2408.01585
- Xiao et al., *Stronger, Faster, and Cheaper Log Parsing with LLMs* (LogBatcher). arXiv:2406.06156
- PIPLUP, *Plug it and Play on Logs: A Configuration-Free Statistic-Based Log Parser*. arXiv:2508.09366
- He et al., *Drain: An Online Log Parsing Approach with Fixed Depth Tree* (ICWS 2017)
- Unsloth: github.com/unslothai/unsloth
