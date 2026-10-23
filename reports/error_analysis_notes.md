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

## Cap-10 run (`ft_r16_cap10`, 1067 train lines instead of 594; same config, val and tests)

- **Grouping improved most:** held-out GA 0.392 -> 0.447 (now above Drain's 0.401), template-disjoint
  0.805 -> 0.846, handcrafted 0.917 -> 0.943. Held-out PA 0.336 -> 0.355, template-disjoint PA flat (0.749),
  handcrafted PA 0.551 -> 0.612. Single seed each, so a +0.02 move may be noise.
- **Per system (held-out PA):** Thunderbird 0.519 -> 0.614, Mac 0.363 -> 0.382, OpenStack 0.354 -> 0.334,
  Proxifier 0.106 -> 0.090.
- **Proxifier learned to mask hosts but mangles one placeholder.** Lines starting with `<*>:<*>` went
  from 300 to 686 of 1056, and distinct predicted templates fell from 365 to 251. But 207 held-out
  predictions (all Proxifier, all wrong) write `(<= KB)` where `(<*> KB)` is meant. That new artefact is
  why "hallucinated" rose from 91 to 447; it is a malformed placeholder, not invented content.
- **Takeaway:** more varied examples per template teach masking (GA up everywhere). The remaining
  Proxifier loss is a gold convention (`<*> close, <*> <*>, <*> <*>` collapses the byte counts) plus the
  `<=` artefact.
