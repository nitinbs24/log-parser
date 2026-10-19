from src.baselines.drain_baseline import drain_templates


def test_drain_keeps_length_and_order_and_masks_variables():
    lines = ["Received block 1 of size 5", "Received block 2 of size 7", "Server started"]
    out = drain_templates(lines)
    assert len(out) == len(lines)
    assert out[0] == out[1] == "Received block <*> of size <*>"
    assert out[2] == "Server started"
