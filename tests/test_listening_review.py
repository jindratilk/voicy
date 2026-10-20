"""Behavior checks for private worksheet bindings and its HTTP boundary."""
import hashlib
from http.client import HTTPConnection
import importlib.util
import json
from pathlib import Path
import threading
import wave

import pytest

SPEC = importlib.util.spec_from_file_location(
    "listening_review", Path(__file__).parents[1] / "scripts/growth/serve_listening_review.py")
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


@pytest.fixture
def packet(tmp_path):
    records, cases = [], []
    for number in range(1, 6):
        versions = []
        for index, variant in enumerate(["reference", "input", "enhanced"]):
            path = tmp_path / f"{number}-{variant}.wav"
            with wave.open(str(path), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(3)
                audio.setframerate(48000)
                audio.writeframes((number * 10 + index).to_bytes(3, "little") * 32)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            records.append({"path": path.name, "sha256": digest, "variant": variant})
            versions.append({"sha256": digest, "frames": 32, "variant": variant})
        cases.append({"case": number, "utterance_id": f"synthetic-{number}",
                      "expected_transcript": "Words <remain> text.",
                      "listening_versions": versions})
    (tmp_path / "MANIFEST.json").write_text(json.dumps({"records": records}))
    results = tmp_path / "results.json"
    results.write_text(json.dumps({"runtime": {"version": "0.3.2"}, "cases": cases}))
    return review.prepare_packet(results, tmp_path, seed=bytes(range(32)))


def test_public_worksheet_conceals_assignments_and_preserves_all_cases(packet):
    public = packet["public"]
    assert len(public["cases"]) == 5
    assert len({clip["token"] for case in public["cases"] for clip in case["clips"]}) == 15
    assert all(set(clip) == {"label", "token"} for c in public["cases"] for clip in c["clips"])
    body, _ = review.render_page(public)
    assert b"Words &lt;remain&gt; text." in body
    assert packet["assignment_seed"].encode() not in body
    assert all(item["path"].encode() not in body for item in packet["assets"].values())
    assert body.count(b'preload="none"') == 15


def test_http_serves_only_verified_clips_and_no_private_packet(packet):
    server = review.make_server(packet, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = HTTPConnection("127.0.0.1", server.server_address[1])
    try:
        connection.request("GET", "/")
        response = connection.getresponse()
        assert response.status == 200
        assert "connect-src 'none'" in response.getheader("Content-Security-Policy")
        assert "assignment_seed" not in response.read().decode()
        token, item = next(iter(packet["assets"].items()))
        connection.request("GET", f"/clips/{token}.wav")
        response = connection.getresponse()
        assert response.status == 200
        assert hashlib.sha256(response.read()).hexdigest() == item["sha256"]
        for path in ["/packet.json", "/MANIFEST.json", "/../results.json", "/clips/%2e%2e/results.json"]:
            connection.request("GET", path)
            response = connection.getresponse()
            assert response.status == 404
            response.read()
        connection.request("GET", "/", headers={"Host": "unrelated.example"})
        response = connection.getresponse()
        assert response.status == 400
        response.read()
        Path(item["path"]).write_bytes(b"changed after startup")
        connection.request("GET", f"/clips/{token}.wav")
        response = connection.getresponse()
        assert response.status == 409
        response.read()
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join()


def test_changed_asset_fails_before_startup(packet):
    item = next(iter(packet["assets"].values()))
    Path(item["path"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        review.make_server(packet, port=0)
