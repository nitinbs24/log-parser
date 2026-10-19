import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from src import predict
from src.predict import clean, parse_lines


def _echo_log(msgs, model, adapter):
    # stub backend: returns the log line unchanged
    return [m[-1]["content"].split("\nLog: ", 1)[1] for m in msgs]


@pytest.fixture
def stub(monkeypatch):
    monkeypatch.setitem(predict.BACKENDS, "stub", _echo_log)


def test_parse_lines_preserves_length_and_order(stub):
    lines = [f"line {i}" for i in range(7)]
    assert parse_lines(lines, "Nginx", backend="stub") == lines


def test_unknown_backend_raises():
    with pytest.raises(ValueError):
        parse_lines(["x"], backend="nope")


@pytest.mark.parametrize("raw,want", [
    ("Server started", "Server started"),
    ("`Server <*> started`", "Server <*> started"),
    ('"Server started"', "Server started"),
    ("```\nServer <*> started\n```", "Server <*> started"),
    ("Server <*> started\nExplanation: the variable is ...", "Server <*> started"),
    ('"<*>" <*> "-"', '"<*>" <*> "-"'),  # quotes that belong to the template stay
    ("", ""),
])
def test_clean(raw, want):
    assert clean(raw) == want


def test_ollama_backend_request_and_response(monkeypatch):
    seen = []

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append(body)
            out = json.dumps({"message": {"content": "T:" + body["messages"][-1]["content"].split("Log: ")[1]}}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setattr(predict, "OLLAMA_URL", f"http://127.0.0.1:{srv.server_port}")
    out = parse_lines(["a 1", "b 2", "c 3"], "Redis", backend="ollama", model="m")
    srv.shutdown()
    assert out == ["T:a 1", "T:b 2", "T:c 3"]
    assert seen[0]["stream"] is False and seen[0]["options"]["temperature"] == 0 and seen[0]["model"] == "m"
