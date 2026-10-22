"""Error analysis over saved predictions (step 5.2): per-system PA, fixed/broke vs the few-shot base, error taxonomy.

Usage: python -m src.error_analysis [--out reports/error_analysis.md]
Reads results/<method>/<split>.csv (columns system, content, gold, pred). A line is correct when
post_process(pred) == post_process(gold), the same rule PA uses.
"""
import argparse
import re
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

from third_party.loghub2_eval.post_process import post_process

METHODS = ["drain", "base_zeroshot", "base_fewshot", "ft_r16"]
SPLITS = ["test_heldout", "test_template_disjoint", "handcrafted"]
CATEGORIES = ["format", "hallucinated", "under-generalised", "over-generalised", "other"]
BASE, FT = "base_fewshot", "ft_r16"
FIXED_BROKE_SHOWN = 20
TOKEN = re.compile(r"<\*>|[^\s<]+|<")


def classify(content, gold, pred):
    """One category for a wrong prediction. Priority: format > hallucinated > under > over > other."""
    pred, gold = str(pred), post_process(gold)
    if not pred.strip() or re.search(r"<(?!\*>)[^<>\s]*>", pred):
        return "format"  # empty, or a placeholder other than <*>
    pp = post_process(pred)
    if any(t and t not in content for t in re.split(r"\s+|<\*>", pp)):
        return "hallucinated"  # a literal that never appears in the input line
    kinds = set()
    g, p = TOKEN.findall(gold), TOKEN.findall(pp)  # <*> is its own token, so "<*>:<*>" vs "host:<*>" aligns
    for op, a0, a1, b0, b1 in SequenceMatcher(None, g, p, autojunk=False).get_opcodes():
        gs, ps = " ".join(g[a0:a1]), " ".join(p[b0:b1])
        if op == "equal":
            continue
        if "<*>" in gs and "<*>" not in ps:
            kinds.add("under-generalised")  # gold masks it, we kept the literal
        elif "<*>" in ps and "<*>" not in gs:
            kinds.add("over-generalised")  # we masked a constant word
    for k in ("under-generalised", "over-generalised"):
        if k in kinds:
            return k
    return "other"


def load(method, split):
    df = pd.read_csv(f"results/{method}/{split}.csv", dtype=str, keep_default_na=False)
    df["ok"] = [post_process(g) == post_process(p) for g, p in zip(df.gold, df.pred)]
    return df


def md(df):
    rows = [[df.index.name or ""] + list(df.columns)] + [[i] + list(r) for i, r in zip(df.index, df.values.tolist())]
    lines = ["| " + " | ".join(map(str, r)) + " |" for r in rows]
    return "\n".join([lines[0], "|" + "---|" * len(rows[0])] + lines[1:])


def report(splits=SPLITS, methods=METHODS):
    out = ["# Error analysis (exact-match correctness, post-processed like PA)\n"]
    for split in splits:
        data = {m: load(m, split) for m in methods if Path(f"results/{m}/{split}.csv").exists()}
        out.append(f"\n## {split}\n\n### PA per system (line-level, not the macro average)\n")
        pa = pd.DataFrame({m: d.groupby("system").ok.mean().round(3) for m, d in data.items()})
        out.append(md(pa) + "\n")
        out.append("\n### Wrong predictions by category\n")
        tax = pd.DataFrame({m: pd.Series([classify(c, g, p) for c, g, p, ok in zip(d.content, d.gold, d.pred, d.ok) if not ok]
                                         ).value_counts().reindex(CATEGORIES, fill_value=0) for m, d in data.items()})
        out.append(md(tax) + "\n")
        if BASE in data and FT in data:
            b, f = data[BASE], data[FT]
            fixed, broke = f[f.ok & ~b.ok], f[~f.ok & b.ok]
            out.append(f"\n### {FT} vs {BASE}: fixed {len(fixed)}, broke {len(broke)} of {len(f)} lines\n")
            for name, rows in (("Fixed", fixed), ("Broke", broke)):
                out.append(f"\n**{name}** (first {FIXED_BROKE_SHOWN} of {len(rows)}, one per distinct gold)\n")
                for _, r in rows.drop_duplicates("gold").head(FIXED_BROKE_SHOWN).iterrows():
                    out.append(f"- `{r.content[:100]}`\n  - gold `{r.gold[:100]}`\n  - {FT} `{r.pred[:100]}`  /  {BASE} `{b.loc[_, 'pred'][:100]}`")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/error_analysis.md")
    args = ap.parse_args()
    Path(args.out).write_text(report())
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
