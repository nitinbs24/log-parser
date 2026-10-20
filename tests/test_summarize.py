import json

from src.summarize import summary


def test_summary_orders_baselines_first_and_skips_missing(tmp_path):
    for method, pa in [("ft_r16", 0.9), ("base_fewshot", 0.5), ("drain", 0.3)]:
        d = tmp_path / method
        d.mkdir()
        (d / "handcrafted.json").write_text(json.dumps({"average": {"GA": 1, "FGA": 1, "PA": pa, "FTA": 1}}))
    text = summary(tmp_path)
    assert text.index("| drain |") < text.index("| base_fewshot |") < text.index("| ft_r16 |")
    assert text.count("| drain |") == 1  # only the split that has a file
