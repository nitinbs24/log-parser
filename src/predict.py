"""One log line in, one template out. `parse_lines` is the only function Phase B imports.

Usage: python -m src.predict --split handcrafted --backend vllm --out results/base/handcrafted.csv
"""
import argparse
import functools
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.data import SPLITS, load_split
from src.prompt import prompt_messages

# ⚠ verify: the Ollama tag depends on what you pulled or imported.
DEFAULT_MODELS = {"vllm": "Qwen/Qwen3-4B-Instruct-2507", "ollama": "qwen3:4b-instruct-2507"}
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def clean(raw):
    """First non-empty line, minus code fences and one pair of wrapping quotes/backticks."""
    lines = [l.strip() for l in raw.splitlines() if l.strip() and not l.strip().startswith("```")]
    out = lines[0] if lines else ""
    for q in "`\"'":
        # only a wrapper: a template that legitimately starts and ends with a quote has that quote inside too
        if len(out) > 1 and out[0] == out[-1] == q and q not in out[1:-1]:
            out = out[1:-1]
    return out


@functools.lru_cache(maxsize=2)
def _vllm_engine(model, lora):
    from vllm import LLM  # imported lazily: vLLM needs CUDA and is absent on the laptop
    return LLM(model, enable_lora=lora, dtype="half", max_model_len=1024)


def _generate_vllm(msgs, model, adapter):
    # ⚠ verify against the installed vLLM: llm.chat and LoRARequest signatures drift
    from vllm import SamplingParams
    from vllm.lora.request import LoRARequest
    sp = SamplingParams(temperature=0, max_tokens=128)
    req = LoRARequest("logparser", 1, adapter) if adapter else None
    outs = _vllm_engine(model, adapter is not None).chat(msgs, sp, lora_request=req)
    return [o.outputs[0].text for o in outs]


def _generate_ollama(msgs, model, adapter):
    assert adapter is None, "Ollama serves a merged model; pass the GGUF as --model instead of --adapter"

    def one(m):
        body = json.dumps({"model": model, "messages": m, "stream": False, "options": {"temperature": 0}}).encode()
        req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.load(r)["message"]["content"]

    with ThreadPoolExecutor(4) as pool:  # CPU inference is slow; a few workers is plenty
        return list(pool.map(one, msgs))


BACKENDS = {"vllm": _generate_vllm, "ollama": _generate_ollama}


def generate(lines, system=None, *, backend="vllm", model=None, adapter=None):
    """Raw model outputs, one per line, before clean()."""
    if backend not in BACKENDS:
        raise ValueError(f"unknown backend {backend!r}")
    msgs = [prompt_messages(system or "unknown", l) for l in lines]
    raw = BACKENDS[backend](msgs, model or DEFAULT_MODELS.get(backend), adapter)
    assert len(raw) == len(lines)
    return raw


def parse_lines(lines, system=None, *, backend="vllm", model=None, adapter=None):
    return [clean(r) for r in generate(lines, system, backend=backend, model=model, adapter=adapter)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=SPLITS)
    ap.add_argument("--out", required=True)
    ap.add_argument("--backend", default="vllm", choices=BACKENDS)
    ap.add_argument("--model")
    ap.add_argument("--adapter")
    ap.add_argument("--limit", type=int, help="first N lines only, for smoke tests")
    args = ap.parse_args()
    df = load_split(SPLITS[args.split])
    if args.limit:
        df = df.head(args.limit)
    df["raw"] = ""
    for system, g in df.groupby("system"):
        df.loc[g.index, "raw"] = generate(g.content.tolist(), system,
                                          backend=args.backend, model=args.model, adapter=args.adapter)
    df["pred"] = df.raw.map(clean)
    changed = int((df.raw.str.strip() != df.pred).sum())
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df[["system", "content", "gold", "pred"]].to_csv(args.out, index=False)
    print(f"{len(df)} lines; clean() changed {changed} ({changed / len(df):.1%})")


if __name__ == "__main__":
    main()
