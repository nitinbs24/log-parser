import json
from pathlib import Path

import yaml

from src.sweep import CONFIG_DIR, SPEC, make_configs, summary

SPEC_DATA = yaml.safe_load(SPEC.read_text())


def test_each_run_changes_only_its_axis_and_keeps_the_seed():
    cfgs, base = make_configs(SPEC_DATA), yaml.safe_load(Path(SPEC_DATA["base"]).read_text())
    assert cfgs["r8"]["lora"]["r"] == 8 and cfgs["r8"]["lora"]["alpha"] == 16
    assert cfgs["lr5e-4"]["train"]["lr"] == 5e-4 and cfgs["lr5e-4"]["train"]["epochs"] == base["train"]["epochs"]
    assert cfgs["no_system"]["system_line"] is False and cfgs["default"]["system_line"] is True
    assert all(c["train"]["seed"] == base["train"]["seed"] for c in cfgs.values())
    assert cfgs["ep5"]["output_dir"] == "outputs/runs/sweep_ep5" and cfgs["ep5"]["run_name"] == "sweep_ep5"


def test_final_weights_are_evaluated_for_every_epoch_count():
    steps_per_epoch = 38  # 594 examples / batch 16, rounded up
    for name, cfg in make_configs(SPEC_DATA).items():
        total = steps_per_epoch * cfg["train"]["epochs"]
        assert total % cfg["train"]["eval_steps"] == 0, name


def test_committed_sweep_configs_match_the_spec():
    for name, cfg in make_configs(SPEC_DATA).items():
        assert yaml.safe_load((CONFIG_DIR / f"{name}.yaml").read_text()) == cfg, f"rerun: python -m src.sweep write ({name})"


def _result(tmp, name, best, step, by_system):
    d = tmp / f"sweep_{name}"
    d.mkdir()
    (d / "result.json").write_text(json.dumps({
        "best_val_pa": best, "best_step": step, "wall_time_min": 7.0, "peak_vram_gb": 7.4,
        "history": {str(step): {"val_pa": best, "val_pa_macro": best - 0.05, "by_system": by_system, "eval_loss": 0.05},
                    "114": {"val_pa": best - 0.1, "val_pa_macro": 0.5, "by_system": by_system, "eval_loss": 0.04}}}))


def test_summary_flags_noise_and_reports_per_system(tmp_path):
    _result(tmp_path, "default", 0.900, 76, {"BGL": 1.0, "HDFS": 0.5})
    _result(tmp_path, "r8", 0.917, 76, {"BGL": 1.0, "HDFS": 0.5})  # one line better: noise
    _result(tmp_path, "r32", 0.800, 57, {"BGL": 1.0, "HDFS": 0.2})
    text = summary(tmp_path, ["default", "r8", "r32", "missing"])
    assert "| r8 | 0.917 | +0.017 (noise)" in text and "| 0.0400 |" in text  # min eval_loss over the history
    assert "| r32 | 0.800 | -0.100 |" in text and "(noise)" not in text.split("| r32")[1].split("\n")[0]
    assert "| r32 | 1.00 | 0.20 |" in text and "missing" not in text
