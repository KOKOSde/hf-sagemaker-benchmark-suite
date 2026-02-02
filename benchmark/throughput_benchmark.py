from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import Any

from benchmark.common import SageMakerRuntimeClient, summarize_throughput, write_results


def _payload_bytes(payload_json: str) -> bytes:
    json.loads(payload_json)
    return payload_json.encode("utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="Measure SageMaker endpoint throughput (requests/sec).")
    p.add_argument("--endpoint-name", required=True)
    p.add_argument("--region", required=True)
    p.add_argument("--payload-json", required=True)
    p.add_argument("--content-type", default="application/json")
    p.add_argument("--accept", default="application/json")
    p.add_argument("--duration-seconds", type=float, default=60.0)
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--warmup", type=int, default=20)
    p.add_argument("--output", default="results/benchmark_results.json")
    args = p.parse_args()

    client = SageMakerRuntimeClient(region=args.region)
    payload = _payload_bytes(args.payload_json)

    # Warmup
    for _ in range(max(args.warmup, 0)):
        try:
            client.invoke(args.endpoint_name, payload, content_type=args.content_type, accept=args.accept)
        except Exception:
            pass

    end_time = time.perf_counter() + args.duration_seconds

    @dataclass
    class Counts:
        requests: int = 0
        successes: int = 0
        errors: int = 0

    def worker() -> Counts:
        local = Counts()
        while time.perf_counter() < end_time:
            local.requests += 1
            try:
                client.invoke(args.endpoint_name, payload, content_type=args.content_type, accept=args.accept)
                local.successes += 1
            except Exception:
                local.errors += 1
        return local

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = [ex.submit(worker) for _ in range(args.concurrency)]
        wait(futs)
    duration = time.perf_counter() - start
    counts = Counts()
    for f in futs:
        local = f.result()
        counts.requests += local.requests
        counts.successes += local.successes
        counts.errors += local.errors

    summary = summarize_throughput(
        duration,
        concurrency=args.concurrency,
        requests=counts.requests,
        successes=counts.successes,
        errors=counts.errors,
    )
    record: dict[str, Any] = {
        "kind": "throughput",
        "endpoint_name": args.endpoint_name,
        "region": args.region,
        "summary": summary.__dict__,
    }
    write_results(args.output, record)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()

