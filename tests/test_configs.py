from pathlib import Path

import pytest
import yaml

CONFIGS = sorted(Path("configs").glob("qwen3*.yaml"))


@pytest.mark.parametrize("path", CONFIGS, ids=lambda p: p.name)
def test_train_config_is_t4_safe_and_consistent(path):
    cfg = yaml.safe_load(path.read_text())
    t = cfg["train"]
    assert t["fp16"] and not t["bf16"], "T4 has no bfloat16"
    assert t["save_steps"] % t["eval_steps"] == 0, "load_best_model_at_end needs save_steps to be a multiple of eval_steps"
    assert not Path(cfg["output_dir"]).is_absolute(), "use outputs/... so checkpoints land on Drive"
    assert "heldout" not in cfg["data"]["train"] + cfg["data"]["val"] and "test" not in cfg["data"]["train"] + cfg["data"]["val"]
