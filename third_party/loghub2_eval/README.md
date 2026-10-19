# loghub2_eval

Evaluation code vendored from [logpai/loghub-2.0](https://github.com/logpai/loghub-2.0), commit `ac4aad2ea86f561e5a0acbc6587fa28b487259f9`.

| File | Upstream path |
|---|---|
| `evaluator.py` (GA, FGA) | `benchmark/logparser/utils/evaluator.py` |
| `PA_calculator.py` (PA) | `benchmark/evaluation/utils/PA_calculator.py` |
| `template_level_analysis.py` (PTA, RTA, FTA) | `benchmark/evaluation/utils/template_level_analysis.py` |
| `common.py` (`correct_single_template`, `is_abstract`) | `benchmark/evaluation/utils/common.py` |

Local changes: `template_level_analysis.py` imports `is_abstract` from `.common` instead of `evaluation.utils.common`; `post_process.py` and `__init__.py` are new.

`post_process` is loghub-2.0's `correct_single_template` (the oracle template-correction rules). The `*_structured_corrected.csv` gold files were produced with it.

## License and citation

The code comes from TA-Eval-Rep (University of Luxembourg), licensed GPL-3.0 (see file headers). The dataset terms are in `LICENSE`. If you use Loghub-2k, cite:

- Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, Michael R. Lyu. *Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics.* ISSRE 2023.
- Zhihan Jiang et al. *A Large-scale Evaluation for Log Parsing Techniques: How Far Are We?* ISSTA 2024 (Loghub-2.0).
- Zhihan Jiang et al. *Guidelines for Assessing the Accuracy of Log Message Template Identification Techniques.* ICSE 2022 (template correction).
