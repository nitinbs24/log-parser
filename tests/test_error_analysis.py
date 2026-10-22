from src.error_analysis import classify


def test_categories():
    c = "host.example.com:443 open"
    assert classify(c, "<*>:<*> open", "<*>:<*> open <NUM>") == "format"
    assert classify(c, "<*>:<*> open", "<*>:<*> opened") == "hallucinated"
    assert classify(c, "<*>:<*> open", "host.example.com:<*> open") == "under-generalised"
    assert classify(c, "<*>:<*> open", "<*>:<*> <*>") == "over-generalised"
