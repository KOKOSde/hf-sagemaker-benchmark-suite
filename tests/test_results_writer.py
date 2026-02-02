import json
from pathlib import Path

from benchmark.common import write_results


def test_write_results_creates_and_appends(tmp_path: Path):
    out = tmp_path / "results.json"
    write_results(out, {"kind": "latency", "summary": {"p50_ms": 1}})
    write_results(out, {"kind": "throughput", "summary": {"rps": 10}})

    data = json.loads(out.read_text(encoding="utf-8"))
    assert "results" in data
    assert len(data["results"]) == 2

