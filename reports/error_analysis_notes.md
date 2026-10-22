# Error analysis: what the tables say (held-out, ft_r16)

Tables: `reports/error_analysis.md` (made by `python -m src.error_analysis`).

- **Fine-tuning fixes format, not generalisation.** Few-shot base: 1190 format violations and 42 hallucinations
  on held-out; ft_r16: 41 and 91. Fixed 424 lines, broke 96. Over- and under-generalised errors stay
  large (about 1200 each) because they are mostly label disagreements, below.
- **OpenStack: one label convention causes most errors.** 1000 of 1548 lines are wrong, and 875+
  of those are the same line shape. Gold is `<*> "GET <*>" status: ...`, the model writes
  `<*> "GET <*> HTTP/1.1" status: ...`. The gold template swallows the protocol into the path wildcard.
  That is not wrong parsing, it is a convention the model cannot know for an unseen system. OpenStack
  PA (0.354) therefore understates quality.
- **Proxifier (PA 0.106, GA 0.001):** 609 of 944 errors are under-generalised. The model keeps
  hostnames and `bytes (KB)` literals where gold has `<*>`, and its 365 distinct templates for 8 gold
  templates destroy GA.
- **Mac:** 490 of 755 errors are under-generalised (e.g. `-_continuousScroll` vs gold `<*>-_continuousScroll`)
  plus 63 hallucinations on long lines. **Thunderbird:** 29 format violations, from `<*-><*>`-style
  mangled placeholders.
- **Implication:** at least 30% of the held-out errors (875 of 2862, OpenStack alone) are convention disputes, not model faults. A
  masking pre-pass for hostnames, numbers with units and `HTTP/x.y` would fix a large share, but
  it is a hand-built layer, so report it as an upper-bound experiment, not as the model.
- **Caveat:** categories come from simple token-diff rules (priority format > hallucinated > under >
  over), so a line with several faults gets one label, and "over-generalised" counted the OpenStack
  lines even though the real cause is the swallowed protocol token.
